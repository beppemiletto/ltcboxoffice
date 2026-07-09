import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .forms import ContactForm

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Verifica reCAPTCHA solo se configurato
            recaptcha_token = request.POST.get('recaptcha_token')
            recaptcha_secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', None)

            if recaptcha_secret and recaptcha_token:
                try:
                    recaptcha_data = {
                        'secret': recaptcha_secret,
                        'response': recaptcha_token
                    }
                    recaptcha_response = requests.post(
                        'https://www.google.com/recaptcha/api/siteverify',
                        data=recaptcha_data,
                        timeout=5
                    )
                    result = recaptcha_response.json()

                    if not result.get('success', False) or result.get('score', 0) < 0.5:
                        messages.error(request, 'Verifica anti-robot fallita. Per favore riprova.')
                        context = {
                            'form': form,
                            'recaptcha_site_key': getattr(settings, 'RECAPTCHA_SITE_KEY', ''),
                        }
                        return render(request, 'contact/contact.html', context)
                except Exception as e:
                    print(f"reCAPTCHA verification error: {e}")
                    # Continua comunque se reCAPTCHA fallisce per motivi tecnici

            # Salva il messaggio
            contact_message = form.save(commit=False)
            contact_message.ip_address = get_client_ip(request)
            contact_message.save()

            # Invia email
            try:
                subject = f"[LTC Box Office] {form.cleaned_data['subject']}"
                message_body = f"""
Nuovo messaggio di contatto ricevuto:

Nome: {form.cleaned_data['name']}
Email: {form.cleaned_data['email']}
Oggetto: {form.cleaned_data['subject']}

Messaggio:
{form.cleaned_data['message']}

---
IP Address: {contact_message.ip_address}
Data e ora: {contact_message.created_at.strftime('%d/%m/%Y alle %H:%M')}
"""

                send_mail(
                    subject,
                    message_body,
                    settings.DEFAULT_FROM_EMAIL,
                    ['ltcboxoffice@teatrocambiano.com', 'info@teatrocambiano.com'],
                    fail_silently=False,
                )

                messages.success(request, 'Il tuo messaggio è stato inviato con successo! Ti risponderemo al più presto.')
                return redirect('home')

            except Exception as e:
                messages.error(request, 'Si è verificato un errore durante l\'invio del messaggio. Per favore riprova più tardi.')
                print(f"Error sending email: {e}")

        else:
            messages.error(request, 'Per favore correggi gli errori nel form.')
    else:
        form = ContactForm()

    context = {
        'form': form,
        'recaptcha_site_key': getattr(settings, 'RECAPTCHA_SITE_KEY', ''),
    }
    return render(request, 'contact/contact.html', context)

def get_client_ip(request):
    """Ottiene l'indirizzo IP del client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
