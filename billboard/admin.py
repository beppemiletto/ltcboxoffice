from django.contrib import admin
from .models import Show, Section, SiaeType, Venue

class ShowAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('shw_title',)}
    list_display = ('shw_title', 'slug', 'shw_code', 'siaetype','is_in_billboard', 'is_active') 

class SectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('id','name', 'slug', 'default_price_full', 'default_price_reduced') 

class SiaeTypeAdmin(admin.ModelAdmin):
    list_display = ('code','description', 'iva') 

class VenueAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'capacity', 'address', 'has_config_file')
    list_filter = ('capacity',)
    search_fields = ('name', 'slug', 'address')
    readonly_fields = ('config_file_format',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'address', 'capacity')
        }),
        ('SIAE Codes', {
            'fields': ('ba_code_siae', 'local_code_siae'),
            'classes': ('collapse',)
        }),
        ('Seating Configuration', {
            'fields': ('configuration_file', 'config_file_format'),
            'description': 'Upload a JSON or XML file to define the seating layout. '
                          'File will be saved for future use with venue management commands.'
        }),
    )
    
    def has_config_file(self, obj):
        """Display if venue has a configuration file"""
        return bool(obj.configuration_file)
    has_config_file.boolean = True
    has_config_file.short_description = 'Config File'
    
    def config_file_format(self, obj):
        """Display configuration file format"""
        return obj.get_config_file_format() or '-'
    config_file_format.short_description = 'Format'
    
    def save_model(self, request, obj, form, change):
        """Custom save to handle configuration file upload"""
        super().save_model(request, obj, form, change)
        
        # Show message about uploaded configuration file
        if obj.configuration_file:
            from django.contrib import messages
            if not change:
                messages.success(
                    request,
                    f'Configuration file "{obj.configuration_file.name}" uploaded successfully. '
                    f'Use management commands to load seats and rows from this file.'
                )
            else:
                messages.info(
                    request,
                    f'Configuration file updated. File: {obj.configuration_file.name}'
                )



# Register your models here.
admin.site.register(Show, ShowAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(SiaeType, SiaeTypeAdmin)
admin.site.register(Venue, VenueAdmin)