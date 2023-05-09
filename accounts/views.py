from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import RegistrationForm
from .models import Account
import random
import string

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
            messages.success(request, 'Nuovo Utente {} correttamente registrato. '.format(email))
            return redirect('register')
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
            auth.login(request, user)
            # messages.success(request, 'Adesso sei loggato come {}'.format(email))
            return redirect('home')
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