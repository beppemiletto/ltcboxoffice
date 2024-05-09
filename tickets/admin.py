from django.contrib import admin
from .models import Ticket

class TicketAdmin(admin.ModelAdmin):
    readonly_fields=('payment',)
    list_display = ['number', 'seat', 'orderevent', 'event', 'status', 'pdf_path',]
    list_filter = ['event',]
    search_fields = ['seat', 'orderevent', 'event', 'number',]
    list_per_page = 50

# Register your models here.
admin.site.register(Ticket, TicketAdmin)
