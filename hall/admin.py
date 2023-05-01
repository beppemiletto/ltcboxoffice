from django.contrib import admin
from .models import Seat, Row

class SeatAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'row', 'num_in_row','number') 

class RowAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'offset_start', 'offset_end') 


# Register your models here.
admin.site.register(Seat, SeatAdmin)
admin.site.register(Row, RowAdmin)
