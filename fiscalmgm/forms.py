from django.forms import ModelForm
from .models import EventFiscalData


class FiscalDataForm(ModelForm):
    class Meta:
        model = EventFiscalData
        exclude = ["event", "printed"]
