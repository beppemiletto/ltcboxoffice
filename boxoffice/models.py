from django.db import models
from store.models import Event
from accounts.models import Account

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

class BoxOfficeTransaction(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seats_sold = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id
    


