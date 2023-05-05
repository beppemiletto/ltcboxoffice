from django.db import models
from store.models import Event

# Generics
ingressi_strings = [
    'Gratuito', # for index == 0
    'Intero', # for index == 1
    'Ridotto', # for index == 1
]


# Create your models here.
class Cart(models.Model):
    cart_id         = models.CharField(max_length=250, blank=True)
    date_added      = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.cart_id

class CartItem(models.Model):
    event           = models.ForeignKey(Event, on_delete=models.CASCADE)
    cart            = models.ForeignKey(Cart, on_delete=models.CASCADE)
    seat            = models.CharField(max_length=3, default='C03')
    ingresso        = models.IntegerField(default=1)
    is_active       = models.BooleanField(default=True)

    def __str__(self) -> str:
        return '{}-{}@{}'.format(self.seat, self.ingresso, self.event.event_slug)
    
    def ingresso_str(self):
        return ingressi_strings[self.ingresso]
    

