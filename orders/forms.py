from django import forms
from django.core.exceptions import ValidationError
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name' , 'phone', 'email', 'address_line_1',
        'address_line_2' , 'post_code', 'city', 'province', 'order_note' ]

    def clean_phone(self):
        """
        Sanitize phone number by removing spaces, dots, dashes, and parentheses.
        Keeps only digits and + prefix.
        Ensures max length of 15 characters.
        """
        phone = self.cleaned_data.get('phone', '').strip()

        if not phone:
            raise ValidationError('Il numero di telefono è obbligatorio.')

        # Remove common formatting characters: spaces, dots, dashes, parentheses, slashes
        phone = phone.replace(' ', '').replace('.', '').replace('-', '').replace('(', '').replace(')', '').replace('/', '')

        # Validate that phone contains only digits and optional + at the beginning
        if not phone:
            raise ValidationError('Il numero di telefono non può essere vuoto.')

        # Check if first character is + and rest are digits
        if phone.startswith('+'):
            if not phone[1:].isdigit():
                raise ValidationError('Il numero di telefono può contenere solo cifre e il prefisso + all\'inizio.')
        elif not phone.isdigit():
            raise ValidationError('Il numero di telefono può contenere solo cifre.')

        # Validate length (E.164 international format max is 15 digits)
        if len(phone) > 15:
            raise ValidationError(
                f'Il numero di telefono è troppo lungo ({len(phone)} caratteri). Massimo 15 caratteri consentiti.'
            )

        if len(phone) < 6:
            raise ValidationError(
                'Il numero di telefono è troppo corto. Minimo 6 caratteri richiesti.'
            )

        return phone