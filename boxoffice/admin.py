from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta
from .models import SellingSeats, PaymentMethod, BoxOfficeTransaction, CustomerProfile, BoxOfficeBookingEvent
import json
import os


def cleanup_abandoned_seats(modeladmin, request, queryset):
    """Azione admin per liberare posti abbandonati selezionati"""
    from django.contrib import messages
    
    # Filtra solo posti non finalizzati
    abandoned = queryset.filter(orderevent__isnull=True)
    count = abandoned.count()
    
    if count == 0:
        messages.warning(request, "Nessun posto abbandonato selezionato (già finalizzati).")
        return
    
    # Raggruppa per evento e aggiorna JSON
    events = {}
    for seat in abandoned:
        if seat.event.id not in events:
            events[seat.event.id] = {'event': seat.event, 'seats': []}
        events[seat.event.id]['seats'].append(seat)
    
    freed = 0
    for event_id, data in events.items():
        event = data['event']
        seats = data['seats']
        
        try:
            json_file_path = os.path.abspath(event.get_json_path())
            with open(json_file_path, 'r') as jfp:
                hall_status = json.load(jfp)
            
            for seat in seats:
                if seat.seat in hall_status and hall_status[seat.seat]['status'] == 4:
                    hall_status[seat.seat]['status'] = 0
                    hall_status[seat.seat]['order'] = ''
                    freed += 1
            
            with open(json_file_path, 'w') as jfp:
                json.dump(hall_status, jfp, indent=2)
        except Exception as e:
            messages.error(request, f"Errore aggiornamento JSON evento {event_id}: {e}")
    
    # Elimina record database
    abandoned.delete()
    
    messages.success(request, f"✓ Liberati {freed} posti in {len(events)} eventi. Eliminati {count} record.")

cleanup_abandoned_seats.short_description = "🧹 Libera posti abbandonati selezionati"


class SellingSeatsAdmin(admin.ModelAdmin):
    list_display = ('event', 'seat', 'orderevent', 'session_preview', 'age_minutes', 'is_abandoned') 
    list_filter = ('event', 'orderevent')
    search_fields = ('seat', 'session_id', 'orderevent')
    actions = [cleanup_abandoned_seats]
    readonly_fields = ('created_at',)
    
    def session_preview(self, obj):
        if obj.session_id:
            return f"{obj.session_id[:8]}..."
        return "-"
    session_preview.short_description = "Session ID"
    
    def age_minutes(self, obj):
        if obj.created_at:
            age = timezone.now() - obj.created_at
            minutes = int(age.total_seconds() / 60)
            
            if minutes > 60:
                hours = minutes // 60
                return format_html('<span style="color: red; font-weight: bold;">{} ore</span>', hours)
            elif minutes > 15:
                return format_html('<span style="color: orange;">{} min</span>', minutes)
            else:
                return f"{minutes} min"
        return "-"
    age_minutes.short_description = "Età"
    
    def is_abandoned(self, obj):
        if not obj.orderevent and obj.created_at:
            age = timezone.now() - obj.created_at
            if age > timedelta(minutes=15):
                return format_html('<span style="color: red;">⚠ ABBANDONATO</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    is_abandoned.short_description = "Stato" 

class PaymentMethodAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('id','name', 'code', 'commission_model', 'account_type') 

class BoxOfficeTransactionAdmin(admin.ModelAdmin):
    list_display = ['event','payment_method','amount_paid', 'status']
    readonly_fields = ['user', 'event', 'seats_sold', 'payment_id', 'payment_method', 'amount_paid']
    list_filter = ['event','payment_method']
    list_filter = ['event','customer']
    list_filter = ['event', 'payment_method']

class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['last_name','first_name','phone_number', 'email', 'city']
    readonly_fields = ['last_name']
    list_filter = ['last_name','first_name', 'city']

class BoxOfficeBookingEventAdmin(admin.ModelAdmin):
    list_display = ['pk','event','event_id','seats_price', 'customer','expired']
    list_filter = ['event','user', 'order']
    list_filter = ['event','customer']


# Register your models here.
admin.site.register(SellingSeats, SellingSeatsAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(BoxOfficeTransaction, BoxOfficeTransactionAdmin)
admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(BoxOfficeBookingEvent, BoxOfficeBookingEventAdmin)

