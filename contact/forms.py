from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    recaptcha_token = forms.CharField(widget=forms.HiddenInput(), required=False)

    # Honeypot: campo invisibile agli utenti reali, i bot tendono a compilarlo
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'autocomplete': 'off',
        'tabindex': '-1',
    }))

    # Timestamp di rendering del form, per scartare submit troppo rapidi (bot)
    form_rendered_at = forms.FloatField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Il tuo nome',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'La tua email',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Oggetto del messaggio',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Scrivi qui il tuo messaggio...',
                'rows': 5,
                'required': True
            }),
        }
        labels = {
            'name': 'Nome',
            'email': 'Email',
            'subject': 'Oggetto',
            'message': 'Messaggio',
        }
