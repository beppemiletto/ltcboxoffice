from django.contrib import admin
from .models import SellingSeats, PaymentMethod, BoxOfficeTransaction

class SellingSeatsAdmin(admin.ModelAdmin):
    list_display = ('event', 'seat', 'orderevent') 

class PaymentMethodAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('id','name', 'code', 'commission_model', 'account_type') 


# Register your models here.
admin.site.register(SellingSeats, SellingSeatsAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(BoxOfficeTransaction)

