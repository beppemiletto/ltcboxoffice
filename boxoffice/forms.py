from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Barcode_Reader(forms.Form):
    barcode_code = forms.CharField(help_text="Enter the barcode code", 
                                   required=True,
                                   initial='', 
                                   max_length= 50, 
                                   min_length=10 )

    def clean_barcode_code(self):
        data:str = self.cleaned_data['barcode_code']

        codes:list = data.split('_')
        if len(codes) == 3:
            print('Valid code detected')
        else:
            raise ValidationError(_(f'Invalid code:{data}'))

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

