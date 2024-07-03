from django.contrib import admin
from .models import SellingSeats, PaymentMethod, BoxOfficeTransaction, CustomerProfile, BoxOfficeBookingEvent

class SellingSeatsAdmin(admin.ModelAdmin):
    list_display = ('event', 'seat', 'orderevent') 

class PaymentMethodAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('id','name', 'code', 'commission_model', 'account_type') 

class BoxOfficeTransactionAdmin(admin.ModelAdmin):
    list_display = ['event','payment_method','amount_paid', 'status']
    readonly_fields = ['user', 'event', 'seats_sold', 'payment_id', 'payment_method', 'amount_paid']
    list_filter = ['event','payment_method']
    list_filter = ['event','customer']
    list_filter = ['event', 'payment_method']

class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['last_name','first_name','phone_number', 'email', 'city']
    readonly_fields = ['last_name']
    list_filter = ['last_name','first_name', 'city']

class BoxOfficeBookingEventAdmin(admin.ModelAdmin):
    list_display = ['pk','event','event_id','seats_price', 'customer','expired']
    list_filter = ['event','user', 'order']
    list_filter = ['event','customer']


# Register your models here.
admin.site.register(SellingSeats, SellingSeatsAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(BoxOfficeTransaction, BoxOfficeTransactionAdmin)
admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(BoxOfficeBookingEvent, BoxOfficeBookingEventAdmin)

