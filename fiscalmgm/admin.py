from django.contrib import admin
from .models import Ingresso, Report, EventFiscalData


class IngressoAdmin(admin.ModelAdmin):
    list_display = ['seat', 'ticket_number','event', 'price', 'sell_mode']
    list_filter = ['event']
    search_fields = ['seat', 'event', 'ticket_number']
    list_per_page = 234

class ReportAdmin(admin.ModelAdmin):
    list_display = ['type','event','progress_number','created_at', 'updated_at']
    list_filter = ['event']
    search_fields = ['type','event','progress_number']
    list_per_page = 234


# Register your models here.
admin.site.register(EventFiscalData)
admin.site.register(Ingresso, IngressoAdmin)
admin.site.register(Report, ReportAdmin)
