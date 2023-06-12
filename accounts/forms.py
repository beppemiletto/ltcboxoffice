from typing import Any, Dict, Mapping, Optional, Type, Union
from  django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Account, UserProfile

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'placeholder': 'Inserisci la password',
            'class': 'form-control'
        }
    ))
    confirm_password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'placeholder': 'Ripeti la password',
            'class': 'form-control'
        }
    ))
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Inserisci il nome'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Inserisci il cognome'
        self.fields['email'].widget.attrs['placeholder'] = 'Inserisci email valida'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Inserisci un numero di telefono'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError('Password does not match!')
        

# USER and UserProfile forms definition

class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'



class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, 
                                       error_messages={'invalid':('Solo file di tipo immagine (png, jpg, tif,...)')},
                                       widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = [  'address_line1', 'address_line2', 'profile_picture',
                  'city', 'province', 'post_code']
 
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'   

