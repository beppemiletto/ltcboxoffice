from django.contrib import admin
from .models import Payment, Order, OrderEvent

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'order_total', 'status', 'is_ordered']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'email', 'phone_number']
    list_per_page = 40

class OrderEventAdmin(admin.ModelAdmin):
    list_display = ['pk','event','event_id','seats_price', 'user']
    list_filter = ['user', 'order', 'event']

# Register your models here.
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderEvent,OrderEventAdmin)
admin.site.register(Payment)
