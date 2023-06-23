from django import forms
from .models import Ticket


class TicketListForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['user']
