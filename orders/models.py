from django.db import models
from accounts.models import Account
from store.models import Event



class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payer_mail = models.CharField(max_length=100, default="")
    payer_id = models.CharField(max_length=100, default="")
    payer_given_name = models.CharField(max_length=100, default="")
    payer_surname = models.CharField(max_length=100, default="")
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id



class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    post_code = models.CharField(max_length=10)
    province = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.FloatField()
    tax = models.FloatField()
    status = models.CharField(max_length=10,choices=STATUS, default='New')
    ip = models.CharField(max_length=20, blank=True)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    def full_name_address(self):
        return "{} {}, \nIndirizzo: {} {}, {} {} - {} \nTelefono {} - Email {}".format(self.first_name, self.last_name,
                                                                            self.address_line_1, self.address_line_2,
                                                                                self.post_code, self.city, self.province,
                                                                                self.phone, self.email)

    def __str__(self):
        if self.user is not None:
            return f"{self.user.last_name}-{self.pk}"
        else:
            return 'A generic Order'


class OrderEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True)
    seats_price = models.CharField(max_length=512, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.event != None:
            return self.event.show.shw_title+'-'+self.event.date_time.strftime("%m/%d/%Y, %H:%M:%S")+'@'+self.user.last_name
        else:
            return ''
        
    def seats_dict(self):
        self.dict_seats = {}
        for item in self.seats_price.split(','):
            seat, ingresso = item.split('$')
            self.dict_seats[seat] = [seat, ingresso]
        return self.dict_seats

class UserEvent(models.Model):
    ordersevents = models.CharField(max_length=100)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True)
    seats_price = models.CharField(max_length=512, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.event != None:
            return self.event.show.shw_title+'-'+self.event.date_time.strftime("%m/%d/%Y, %H:%M:%S")+'@'+self.user.last_name
        else:
            return ''
        
    def seats_dict(self):
        self.dict_seats = {}
        for item in self.seats_price.split(','):
            seat, ingresso = item.split('$')
            self.dict_seats[seat] = [seat, ingresso]
        return self.dict_seats


        
    