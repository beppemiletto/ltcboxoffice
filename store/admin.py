from django.contrib import admin
from .models import Event

# Register your models here.
class EventAdmin(admin.ModelAdmin):
    my_slug = 'my_calculated_slug_string'
    list_display = ('show', 'event_slug', 'date_time') 

admin.site.register(Event, EventAdmin)