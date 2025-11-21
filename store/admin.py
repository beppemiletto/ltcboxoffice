from django.contrib import admin
from .models import Event
from billboard.models import Show, Venue

# Register your models here.
class EventAdmin(admin.ModelAdmin):
    my_slug = 'my_calculated_slug_string'
    list_display = ('show', 'event_slug', 'date_time', 'booking_deadline_hours', 'venue') 
    list_filter = ('venue', 'date_time')
    search_fields = ('show__shw_title', 'event_slug')
    
    fieldsets = (
        ('Event Information', {
            'fields': ('show', 'date_time', 'venue')
        }),
        ('Pricing', {
            'fields': ('price_full', 'price_reduced', 'vat_rate')
        }),
        ('Booking Settings', {
            'fields': ('booking_deadline_hours',),
            'description': 'Configura quante ore prima dello spettacolo chiudere le prenotazioni online (1-24 ore)'
        }),
        ('Status', {
            'fields': ('sold_out',)
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "show":
            kwargs["queryset"] = Show.objects.filter(is_in_billboard=True)
        elif db_field.name == "venue":
            # Set Teatro Cambiano as default
            teatro_cambiano = Venue.objects.filter(slug='teatro-cambiano').first()
            if teatro_cambiano:
                kwargs["initial"] = teatro_cambiano.pk
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Event, EventAdmin)