from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import RegistrationForm
from .models import Account
from carts.models import Cart, CartItem
from carts.views import _cart_id
import random
import string

# verification mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, filepath_to_uri
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.core.mail import EmailMessage

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    # print("Random string of length", length, "is:", result_str)
    return result_str

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            username = email.split('@')[0]+'_'+get_random_string(8)
            user = Account.objects.create_user(first_name=first_name, 
                            last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # user activation
            current_site = get_current_site(request)
            mail_subject = 'LTCBoxOffice - Attivazione utente sul sito {}'.format(current_site.name)
            message_body = render_to_string('accounts/account_verification_email.html',{
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_mail = EmailMessage(mail_subject,message_body, to=[to_email])
            send_mail.send()
            
            return redirect('/accounts/login/?command=verification&email='+email)
    else:

        form = RegistrationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart = cart).exists()
                if is_cart_item_exists:
                    cart_items = CartItem.objects.filter(cart=cart)
                    for item in cart_items:
                        item.user = user
                        item.save()

            except:
                pass
            auth.login(request, user)
            messages.success(request, 'Adesso sei loggato come {}'.format(email))
            return redirect('dashboard')
        else:
            messages.error(request, 'Le credenziali fornite non sono valide')
            return redirect('login')


    return render(request, 'accounts/login.html')

@login_required(login_url= 'login')
def logout(request):
    user_mail = request.user.email
    auth.logout(request)
    messages.success(request,"L'utente {} è stato disconnesso! Arrivederci".format(user_mail))
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist) as e:
        user = None 
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request,"Congratulazioni! L'utente {} è stato correttamente attivato! Buona navigazione!".format(user.email))
        return redirect('login')
    else:
        messages.error(request,"L'utente {} non è stato attivato! Mail di conferma non riconosciuta".format(user.email))
        return redirect('register')

    return HttpResponse('<H1>Questo uidb64 {}, questo token {}</H1>'.format(uidb64, token))

@login_required(login_url= 'login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__iexact=email)
            # user reset lost password
            current_site = get_current_site(request)
            mail_subject = 'LTCBoxOffice - Reset password utente sul sito {}'.format(current_site.name)
            message_body = render_to_string('accounts/reset_password_email.html',{
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_mail = EmailMessage(mail_subject,message_body, to=[to_email])
            send_mail.send()
            messages.success(request,"Una mail è stata inviata a {} per effettuare il reset della password".format(email))
            
            return redirect('login')
        else:
            messages.error(request,"Non esiste nessun utente registrato con indirizzo mail {}.".format(email))
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist) as e:
        user = None 
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request,"Per favore resetta la tua password!")
        return redirect('resetPassword')
    else:
        messages.error(request,"Il link usato non è stato riconosciuto.")
        return redirect('forgotPassword')
    
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,"La password è stata cambiata con successo!")
            return redirect('login')

        else:
            messages.error(request,"Le password non sono uguali, prego correggi.")
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')

