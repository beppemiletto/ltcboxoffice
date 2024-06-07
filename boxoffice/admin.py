from django.contrib import admin
from .models import SellingSeats, PaymentMethod, BoxOfficeTransaction, CustomerProfile, BoxOfficeBookingEvent

class SellingSeatsAdmin(admin.ModelAdmin):
    list_display = ('event', 'seat', 'orderevent') 

class PaymentMethodAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('id','name', 'code', 'commission_model', 'account_type') 

class BoxOfficeBookingEventAdmin(admin.ModelAdmin):
    list_display = ['pk','event','event_id','seats_price', 'customer','expired']
    list_filter = ['event','user', 'order']
    list_filter = ['event','customer']


# Register your models here.
admin.site.register(SellingSeats, SellingSeatsAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(BoxOfficeTransaction)
admin.site.register(CustomerProfile)
admin.site.register(BoxOfficeBookingEvent, BoxOfficeBookingEventAdmin)

