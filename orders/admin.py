from django.contrib import admin
from .models import Payment, Order, OrderEvent, UserEvent, OrderEventLog

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



class OrderEventLogAdmin(admin.ModelAdmin):
    list_display  = ['timestamp', 'orderevent', 'get_operation', 'operator', 'notes', 'ip_address']
    list_filter   = ['operation', 'operator']
    search_fields = ['orderevent__orderevent_number', 'operator__email', 'notes']
    readonly_fields = ['orderevent', 'operation', 'timestamp', 'operator', 'notes', 'ip_address']
    date_hierarchy = 'timestamp'
    list_per_page = 50

    def get_operation(self, obj):
        return obj.get_operation_display()
    get_operation.short_description = 'Operazione'

# Register your models here.
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderEvent, OrderEventAdmin)
admin.site.register(UserEvent, UserEventAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(OrderEventLog, OrderEventLogAdmin)
