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
    
class EventFiscalData(models.Model):
    event = models.OneToOneField(Event,on_delete=models.CASCADE, blank=True, null= True)
    casher_01 = models.CharField(verbose_name= "Nome e cognome persona in cassa 1" , max_length=50, default='Nome Cognome1')
    casher_02 = models.CharField(verbose_name= "Nome e cognome persona in cassa 2" , max_length=50, default='Nome Cognome2')
    intero_ticket_serie_1             = models.CharField(max_length=10, default='')
    intero_ticket_start_number_1      = models.IntegerField(verbose_name='Intero dal numero', default=0, null=True)
    intero_ticket_end_number_1        = models.IntegerField(verbose_name='Intero al numero', default=0, null=True)
    ridotto_ticket_serie_1            = models.CharField(max_length=10, default='')
    ridotto_ticket_start_number_1     = models.IntegerField(verbose_name='Ridotto dal numero', default=0, null=True)
    ridotto_ticket_end_number_1       = models.IntegerField(verbose_name='Ridotto al numero', default=0, null=True)
    gratuito_ticket_serie_1           = models.CharField(max_length=10, default='')
    gratuito_ticket_start_number_1    = models.IntegerField(verbose_name='Gratuito dal numero', default=0, null=True)
    gratuito_ticket_end_number_1      = models.IntegerField(verbose_name='Gratuito al numero', default=0, null=True)
    intero_ticket_serie_2             = models.CharField(max_length=10, default='nd')
    intero_ticket_start_number_2      = models.IntegerField(verbose_name='Intero dal numero', default=0, null=True)
    intero_ticket_end_number_2        = models.IntegerField(verbose_name='Intero al numero', default=0, null=True)
    ridotto_ticket_serie_2            = models.CharField(max_length=10, default='nd')
    ridotto_ticket_start_number_2     = models.IntegerField(verbose_name='Ridotto dal numero', default=0, null=True)
    ridotto_ticket_end_number_2       = models.IntegerField(verbose_name='Ridotto al numero', default=0, null=True)
    gratuito_ticket_serie_2           = models.CharField(max_length=10, default='nd')
    gratuito_ticket_start_number_2    = models.IntegerField(verbose_name='Gratuito dal numero', default=0, null=True)
    gratuito_ticket_end_number_2      = models.IntegerField(verbose_name='Gratuito al numero', default=0, null=True)
    cash_begin_200euro           = models.SmallIntegerField(verbose_name='Num. Inizio 200 Euro', default=0, null=True)
    cash_begin_100euro           = models.SmallIntegerField(verbose_name='Num. Inizio 100 Euro', default=0, null=True)
    cash_begin_50euro           = models.SmallIntegerField(verbose_name='Num. Inizio 50 Euro', default=0, null=True)
    cash_begin_20euro           = models.SmallIntegerField(verbose_name='Num. Inizio 20 Euro', default=0, null=True)
    cash_begin_10euro           = models.SmallIntegerField(verbose_name='Num. Inizio 10 Euro', default=0, null=True)
    cash_begin_5euro           = models.SmallIntegerField(verbose_name='Num. Inizio 5 Euro', default=0, null=True)
    cash_begin_2euro           = models.SmallIntegerField(verbose_name='Num. Inizio 2 Euro', default=0, null=True)
    cash_begin_1euro           = models.SmallIntegerField(verbose_name='Num. Inizio 1 Euro', default=0, null=True)
    cash_begin_50cent           = models.SmallIntegerField(verbose_name='Num. Inizio 50 Cent', default=0, null=True)
    cash_begin_20cent           = models.SmallIntegerField(verbose_name='Num. Inizio 20 Cent', default=0, null=True)
    cash_begin_10cent           = models.SmallIntegerField(verbose_name='Num. Inizio 10 Cent', default=0, null=True)
    cash_end_200euro           = models.SmallIntegerField(verbose_name='Num. Fine 200 Euro', default=0, null=True)
    cash_end_100euro           = models.SmallIntegerField(verbose_name='Num. Fine 100 Euro', default=0, null=True)
    cash_end_50euro           = models.SmallIntegerField(verbose_name='Num. Fine 50 Euro', default=0, null=True)
    cash_end_20euro           = models.SmallIntegerField(verbose_name='Num. Fine 20 Euro', default=0, null=True)
    cash_end_10euro           = models.SmallIntegerField(verbose_name='Num. Fine 10 Euro', default=0, null=True)
    cash_end_5euro           = models.SmallIntegerField(verbose_name='Num. Fine 5 Euro', default=0, null=True)
    cash_end_2euro           = models.SmallIntegerField(verbose_name='Num. Fine 2 Euro', default=0, null=True)
    cash_end_1euro           = models.SmallIntegerField(verbose_name='Num. Fine 1 Euro', default=0, null=True)
    cash_end_50cent           = models.SmallIntegerField(verbose_name='Num. Fine 50 Cent', default=0, null=True)
    cash_end_20cent           = models.SmallIntegerField(verbose_name='Num. Fine 20 Cent', default=0, null=True)
    cash_end_10cent           = models.SmallIntegerField(verbose_name='Num. Fine 10 Cent', default=0, null=True)
    collection_satispay           = models.FloatField(verbose_name='Incasso Satispay Euro', default=0.0, null=True)
    collection_sumup           = models.FloatField(verbose_name='Incasso Sumup Euro', default=0.0, null=True)
    collection_others           = models.FloatField(verbose_name='Incasso Altri Euro', default=0.0, null=True)
    collection_presell          = models.FloatField(verbose_name='Prevendita Euro', default=0.0, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now= True , blank=True)
    printed = models.BooleanField(default= False)

    def __str__(self) -> str:
        if self.pk is not None:
            return 'pk = {} - {} - created = {} - printed = {}'.format(self.pk, self.event, self.created_at, self.printed)
        else:
            return ''