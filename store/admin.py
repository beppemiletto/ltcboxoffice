from django.contrib import admin
from .models import Event
from billboard.models import Show

# Register your models here.
class EventAdmin(admin.ModelAdmin):
    my_slug = 'my_calculated_slug_string'
    list_display = ('show', 'event_slug', 'date_time') 
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "show":
            kwargs["queryset"] = Show.objects.filter(is_in_billboard=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Event, EventAdmin)