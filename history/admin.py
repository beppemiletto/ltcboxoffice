from django.contrib import admin
from .models import HistoryShow, Season

class HistoryShowAdmin(admin.ModelAdmin):
    prepopulated_fields = {'shw_slug': ('shw_title',)}
    list_display = ('shw_title', 'shw_date', 'shw_siaetype','shw_season') 
    search_fields = ['shw_season_id__season_label', 'shw_title']

class SeasonAdmin(admin.ModelAdmin):
    list_display = ('season_label', 'season_start_date','season_end_date')


# Register your models here.
admin.site.register(HistoryShow, HistoryShowAdmin)
admin.site.register(Season, SeasonAdmin)
