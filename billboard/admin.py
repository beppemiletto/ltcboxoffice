from django.contrib import admin
from .models import Show, Section

class ShowAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('shw_title',)}
    list_display = ('shw_title', 'slug', 'shw_code', 'is_in_billboard', 'is_active') 

class SectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('id','name', 'slug', 'default_price_full', 'default_price_reduced') 


# Register your models here.
admin.site.register(Show, ShowAdmin)
admin.site.register(Section, SectionAdmin)