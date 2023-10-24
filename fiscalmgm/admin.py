from django.contrib import admin
from .models import Ingresso


class IngressoAdmin(admin.ModelAdmin):
    list_display = ['seat', 'ticket_number','event', 'price', 'sell_mode']
    list_filter = ['event']
    search_fields = ['seat', 'event', 'ticket_number']
    list_per_page = 234


# Register your models here.
admin.site.register(Ingresso, IngressoAdmin)
