from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.boxoffice, name='boxoffice'),
    path('user_not_allowed/', views.user_not_allowed, name='user_not_allowed'),
    path('event/<int:event_id>/', views.event, name='event'),
    path('boxoffice_cart/<int:event_id>/', views.boxoffice_cart, name='boxoffice_cart'),
    path('boxoffice_plus_price/<int:item_id>/', views.boxoffice_plus_price, name='boxoffice_plus_price'),
    path('boxoffice_minus_price/<int:item_id>/', views.boxoffice_minus_price, name='boxoffice_minus_price'),
    path('boxoffice_remove_cart/<int:item_id>/', views.boxoffice_remove_cart, name='boxoffice_remove_cart'),
] 