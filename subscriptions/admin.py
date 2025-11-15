from django.contrib import admin
from .models import SubscriptionType, Subscription, SubscriptionUsage


@admin.register(SubscriptionType)
class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code_prefix', 'type', 'price', 'discount_percent', 'max_events', 'valid_days', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'code_prefix', 'description']
    list_editable = ['is_active']
    list_per_page = 20


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['subscription_number', 'user', 'subscription_type', 'status', 'valid_from', 'valid_to', 'events_used', 'events_included', 'remaining_display']
    list_filter = ['status', 'subscription_type', 'valid_from', 'valid_to']
    search_fields = ['subscription_number', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['subscription_number', 'created_at', 'updated_at', 'events_used', 'remaining_display']
    list_per_page = 30
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('subscription_number', 'user', 'subscription_type', 'status')
        }),
        ('Validità', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Utilizzo Eventi', {
            'fields': ('events_included', 'events_used', 'remaining_display')
        }),
        ('Pagamento e Barcode', {
            'fields': ('payment', 'barcode_path')
        }),
        ('Note', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def remaining_display(self, obj):
        remaining = obj.remaining_events()
        if remaining == 0:
            return f'✗ {remaining} (Esaurito)'
        elif remaining <= 2:
            return f'⚠ {remaining}'
        else:
            return f'✓ {remaining}'
    remaining_display.short_description = 'Eventi Rimanenti'


@admin.register(SubscriptionUsage)
class SubscriptionUsageAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'event', 'seat', 'used_at', 'used_by']
    list_filter = ['event', 'used_at', 'subscription__subscription_type']
    search_fields = ['subscription__subscription_number', 'event__show__shw_title', 'seat']
    readonly_fields = ['used_at']
    list_per_page = 50
    date_hierarchy = 'used_at'
    
    fieldsets = (
        ('Abbonamento e Evento', {
            'fields': ('subscription', 'event', 'seat')
        }),
        ('Validazione', {
            'fields': ('used_at', 'used_by', 'payment')
        }),
        ('Note', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
