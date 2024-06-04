from django.db import models
from store.models import Event
from accounts.models import Account
from orders.models import OrderEvent, Payment

class SellingSeats(models.Model):
    PRICES = (
        (0,'Gratuito'),
        (1, 'Ridotto'),
        (2, 'Intero'),
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    orderevent = models.CharField(max_length=25, blank=True, null=True, default="") 
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

    def __str__(self):
        return self.name

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
    
class CustomerProfile(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=20, blank=True)
    post_code = models.CharField(max_length=10, blank=True)
    email     = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} - {self.city}"
    
    def full_address(self):
        return f'{self.address}, {self.post_code} - {self.city} ({self.province})'
    
class BoxOfficeBookingEvent(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    event = models.ForeignKey('store.Event', on_delete=models.CASCADE, blank=True, null=True)
    seats_price = models.CharField(max_length=512, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    booking_number = models.CharField(max_length=50, null=True, blank=True)
    expired = models.BooleanField(default = False, blank=True, null=True)

    def __str__(self):
        if self.event != None:
            return self.event.show.slug+'-'+self.event.date_time.strftime("%d/%m/%Y, %H:%M:%S")+'@'+self.customer.last_name
        else:
            return ''
        
    def seats_list(self):
        self.dict_seats = {}
        for item in self.seats_price.split(','):
            seat, ingresso = item.split('$')
            self.dict_seats[seat] = [seat, ingresso]
        return self.dict_seats

    def seats_list_name(self):
        self.list_seats = []
        for item in self.seats_price.split(','):
            seat, ingresso = item.split('$')
            self.list_seats.append(seat)
        return self.list_seats
    
    def seats_dicts(self):
        self.dict_seats = {}
        for item in self.seats_price.split(','):
            seat, ingresso = item.split('$')
            self.dict_seats[seat] = {'seat':seat, 'ingresso':ingresso}
        return self.dict_seats
    
    def seats_count(self):
        return len(self.seats_price.split(','))