from django.db import models
from hall.models import Seat
from accounts.models import Account
from orders.models import Payment, OrderEvent
from store.models import Event
from ltcboxoffice.settings import MEDIA_ROOT, MEDIA_URL
import os

# Create your models here.
class Ticket(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Printed', 'Printed'),
        ('Obliterated', 'Obliterated'),
        ('Cancelled', 'Cancelled'),
    )
    SELLING_MODE = (
        ('W', 'Web'),
        ('C', 'Cassa'),
        ('P', 'Prenotazione'),
    )
    number = models.CharField(max_length=25, blank=True, default='')
    seat = models.CharField(max_length=3, editable= False, blank=True, default='C03')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True, null=True)
    orderevent = models.ForeignKey(OrderEvent,on_delete=models.CASCADE,editable=False, blank=True, default=20, null= True)
    event = models.ForeignKey(Event,on_delete=models.CASCADE,editable=True, blank=True, null= True)
    price = models.IntegerField()
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, blank=True, null=True)
    sell_mode = models.CharField(max_length=12,choices=SELLING_MODE, default='W')
    status = models.CharField(max_length=12,choices=STATUS, default='New')
    pdf_path = models.FilePathField(path=MEDIA_ROOT / 'tickets' , verbose_name='pdf file path', default='dummy.pdf', editable=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self) -> str:
        if self.orderevent is not None:
            return '{} - {} - {} - {}'.format(self.pk,self.orderevent.event.show.shw_title, self.orderevent.event.date_time,self.user.last_name)
        else:
            return ''
    
    def abs_path(self) -> str:
        abs_pdf_path = f"{MEDIA_ROOT / 'tickets' / self.pdf_path}"
        return abs_pdf_path
    

    