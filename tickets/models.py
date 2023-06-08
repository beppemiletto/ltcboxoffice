from django.db import models
from hall.models import Seat
from accounts.models import Account
from orders.models import Payment, OrderEvent

# Create your models here.
class Ticket(models.Model):
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, editable= False)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    orderevent = models.ForeignKey(OrderEvent,on_delete=models.CASCADE,editable=False, blank=True, default=20)
    price = models.IntegerField()
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return '{} - {} - {} - {}'.format(self.pk,self.orderevent.event.show.shw_title, self.event.date_time,self.user.last_name)