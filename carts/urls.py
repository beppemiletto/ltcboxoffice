from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.cart, name='cart'),
    path('add_cart/<int:event_id>/', views.add_cart, name='add_cart'),
] 