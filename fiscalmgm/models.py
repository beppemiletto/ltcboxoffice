from django.db import models
from store.models import Event
from ltcboxoffice.settings import MEDIA_ROOT, MEDIA_URL

# Create your models here.
class Ingresso(models.Model):
    ticket_number = models.CharField(max_length=25, blank=True, default='')
    seat = models.CharField(max_length=3, editable= False, blank=True, default='C03')
    event = models.ForeignKey(Event,on_delete=models.CASCADE,editable=True, blank=True, null= True)
    price = models.FloatField()
    sell_mode = models.CharField(max_length=12, default='Cassa')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self) -> str:
        if self.pk is not None:
            return '{} - {} - {} - {}'.format(self.pk,self.seat, self.price,self.created_at)
        else:
            return ''