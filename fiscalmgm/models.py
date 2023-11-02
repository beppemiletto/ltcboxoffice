from django.db import models
from store.models import Event
from ltcboxoffice.settings import MEDIA_ROOT, MEDIA_URL
import os

# Create your models here.
class Ingresso(models.Model):
    ticket_number = models.CharField(max_length=25, blank=True, default='')
    seat = models.CharField(max_length=3, editable= False, blank=True, default='C03')
    event = models.ForeignKey(Event,on_delete=models.CASCADE,editable=True, blank=True, null= True)
    price = models.FloatField()
    sell_mode = models.CharField(max_length=12, default='Cassa')
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now= True , blank=True)

    def __str__(self) -> str:
        if self.pk is not None:
            return '{} - {} - {} - {}'.format(self.pk,self.seat, self.price,self.created_at)
        else:
            return ''
        

class Report(models.Model):
    event = models.ForeignKey(Event,on_delete=models.CASCADE,editable=True, blank=True, null= True)
    type = models.CharField(max_length=12, default='SIAE MOD 566')
    progress_number = models.PositiveIntegerField(editable=True, blank=True, null= True, default= 0)
    doc_path = models.FilePathField(path=MEDIA_ROOT / 'siae_reports' , verbose_name='report file path', default='dummy.xls', editable=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now= True , blank=True)

    def __str__(self) -> str:
        if self.pk is not None:
            return '{} - {} - {} - {}'.format(self.pk,self.type, self.event,self.created_at)
        else:
            return ''
    
        
    def abs_path(self) -> str:
        abs_doc_path = f"{MEDIA_ROOT / 'siae_reports' / self.doc_path}"
        return abs_doc_path