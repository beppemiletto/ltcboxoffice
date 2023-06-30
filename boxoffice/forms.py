from django import forms
from .models import SellingSeats


class SellingForm(forms.ModelForm):
    class Meta:
        model = SellingSeats
        fields = ['seat', 'price' ]