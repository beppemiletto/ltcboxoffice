from django.db import models
from store.models import Event

# Create your models here.
class SellingSeats(models.Model):
    PRICES = (
        (0,'Gratuito'),
        (1, 'Ridotto'),
        (2, 'Intero'),
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seat = models.CharField(max_length=3,verbose_name='Posto')
    price = models.IntegerField(choices=PRICES, default=0)
    cost = models.FloatField(default=0.0)
    ingresso = models.CharField(max_length=12, default="Gratuito")
    


