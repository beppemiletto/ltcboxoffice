from django.contrib import admin
from .models import Payment, Order, OrderEvent, UserEvent

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'order_total', 'status', 'is_ordered']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'email', 'phone_number']
    list_per_page = 40

class OrderEventAdmin(admin.ModelAdmin):
    list_display = ['pk','event','event_id','seats_price', 'user','order', 'expired']
    list_filter = ['event','user', 'order']

class UserEventAdmin(admin.ModelAdmin):
    list_display = ['pk','event','user','ordersevents']
    list_filter = ['user', 'event']

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['pk','user','status','amount_paid', 'payment_method',]
    list_filter = ['user', 'status']



# Register your models here.
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderEvent,OrderEventAdmin)
admin.site.register(UserEvent,UserEventAdmin)
admin.site.register(Payment, PaymentAdmin)
