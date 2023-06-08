from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.tickets, name='tickets'),
    path('event_list/<slug:event_slug>/', views.event_list, name='event_list'),
    path('print_ticket/<int:orderevent>/', views.print_ticket, name='print_ticket'),
] 