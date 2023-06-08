from django.contrib import admin
from django.db import models
from store.models import Event
from accounts.models import Account

# Generics
ingressi_strings = [
    'Gratuito', # for index == 0
    'Intero', # for index == 1
    'Ridotto', # for index == 2
]


# Create your models here.
class Cart(models.Model):
    cart_id         = models.CharField(max_length=250, blank=True)
    date_added      = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.cart_id

class CartItem(models.Model):
    INGRESSI = ((0,'Gratuito'), (1,'Intero'), (2,'Ridotto'),)
    user            = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    event           = models.ForeignKey(Event, on_delete=models.CASCADE)
    cart            = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    seat            = models.CharField(max_length=3, default='C03')
    ingresso        = models.IntegerField( choices=INGRESSI,default=1)
    price           = models.FloatField(default = 0.0, blank=True)
    is_active       = models.BooleanField(default=True)

    def __str__(self) -> str:
        return '{}-{}@{}'.format(self.seat, self.ingresso, self.event.event_slug)
    
    def ingresso_str(self):
        return ingressi_strings[self.ingresso]
    
    def item_record(self):
        return('{}-{}'.format(self.event.pk, self.seat))
    
    @admin.display
    def cart_item_extended_name(self):
        return('{}-{} seat {}'.format(self.event,self.event.pk, self.seat))
    

