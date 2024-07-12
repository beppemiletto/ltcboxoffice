from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.store, name='store'),
    path('section/<slug:section_slug>/', views.store, name='shows_by_section'),
    path('section/<slug:section_slug>/<slug:show_slug>/', views.show_detail, name='show_detail'),
    path('show/<str:showcode>/', views.show_detail_showcode, name='show_detail_showcode'),
    path('section/<slug:section_slug>/<slug:show_slug>/<slug:event_slug>/', views.select_seats, name='select_seats'),
    path('search/', views.search, name='search'),
] 
