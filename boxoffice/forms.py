from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

class Barcode_Reader(forms.Form):
    """Form per lettura QR Code delle prenotazioni"""
    barcode_code = forms.CharField(help_text="Inserisci il codice del QR Code",
                                   required=True,
                                   initial='',
                                   max_length= 50,
                                   min_length=10 )

    def clean_barcode_code(self):
        data:str = self.cleaned_data['barcode_code']
        lenghts = [5,6,6]


        codes:list = re.split('[_?]',data)
        if len(codes) == 3:
            print('Valid QR code detected')
            for idx, code in enumerate(codes):
                if len(code) < lenghts[idx]:
                    raise ValidationError(_(f'Codice QR non valido: {code} in {data}. Riprova.'))

        else:
            raise ValidationError(_(f'Codice QR non valido: {data}'))

        # Remember to always return the cleaned data.
        return data
    
class OrderEventForm(forms.Form):
    barcode_code = forms.CharField()
    user = forms.CharField()
    event = forms.CharField()
    seats_price = forms.CharField(label='Evento')
    created_at = forms.DateTimeField(label="Data di creazione")
    updated_at = forms.DateTimeField(label="Data di aggiornamento")
    expired = forms.BooleanField(label='Ordine evaso', required=False)

class CustomerProfileForm(forms.Form):
    first_name   = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name    = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address      = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city         = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    province     = forms.CharField(max_length=20,  required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    post_code    = forms.CharField(max_length=10,  required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email        = forms.EmailField(max_length=100, required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=50,  required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class CustomerShortForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    email     = forms.EmailField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=50, required=False)
