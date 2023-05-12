from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.cart, name='cart'),
    path('add_cart/<int:event_id>/', views.add_cart, name='add_cart'),
    path('plus_ingresso/<int:item_id>/', views.plus_ingresso, name='plus_ingresso'),
    path('minus_ingresso/<int:item_id>/', views.minus_ingresso, name='minus_ingresso'),
    path('remove_cart/<int:item_id>/', views.remove_cart, name='remove_cart'),
    path('checkout/', views.checkout, name='checkout'),
] 