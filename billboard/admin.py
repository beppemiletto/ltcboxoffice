from django.contrib import admin
from .models import Show

class ShowAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('shw_title',)}
    list_display = ('shw_title', 'slug', 'shw_code', 'is_in_billboard') 

# Register your models here.
admin.site.register(Show, ShowAdmin)