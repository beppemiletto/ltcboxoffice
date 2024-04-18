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
    prepopulated_fields = {'slug':('name',)}



# Register your models here.
admin.site.register(Show, ShowAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(SiaeType, SiaeTypeAdmin)
admin.site.register(Venue, VenueAdmin)