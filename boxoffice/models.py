from django.db import models
from store.models import Event
from accounts.models import Account
from orders.models import OrderEvent

class SellingSeats(models.Model):
    PRICES = (
        (0,'Gratuito'),
        (1, 'Ridotto'),
        (2, 'Intero'),
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    orderevent = models.ForeignKey(OrderEvent, on_delete=models.CASCADE, blank=True, null=True) 
    seat = models.CharField(max_length=3,verbose_name='Posto')
    price = models.IntegerField(choices=PRICES, default=0)
    cost = models.FloatField(default=0.0)
    ingresso = models.CharField(max_length=12, default="Gratuito")

class PaymentMethod(models.Model):
    ACCOUNT_TYPES= (
        (0,'Cassa'),
        (1,'Bank'),
        (2,'Satispay'),
        (3,'Sumup'),
    )
    COMMISSION_MODELS = (
        (0,'No commission'),
        (1,'Perc 2%'),
        (2,'Fixed on threshold 10 Euro'),
    )
    name = models.CharField(max_length=25 )
    slug = models.SlugField(max_length=25, unique=True)
    code = models.CharField(max_length=50, null=True, blank=True)
    account_type = models.IntegerField(choices=ACCOUNT_TYPES, default=0)
    commission_model =  models.IntegerField(choices=COMMISSION_MODELS, default=0)


class BoxOfficeTransaction(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seats_sold = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=100)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, null=True, blank=True)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id