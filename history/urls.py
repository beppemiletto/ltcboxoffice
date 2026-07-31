from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.history_home,    name='history_home'),
    path('registi/',                      views.directors_list,  name='history_directors'),
    path('stagione/<str:season_label>/',  views.season_detail,   name='history_season'),
    path('regista/<slug:slug>/',          views.director_detail, name='history_director'),
    path('spettacolo/<slug:slug>/',       views.show_detail,     name='history_show'),
]
