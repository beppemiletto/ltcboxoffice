from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.bookings, name='bookings'),
    path('add_booking/<int:event_id>/', views.add_booking, name='add_booking'),
    path('plus_ing_booking/<int:item_id>/', views.plus_ing_booking, name='plus_ing_booking'),
    path('minus_ing_booking/<int:item_id>/', views.minus_ing_booking, name='minus_ing_booking'),
    path('remove_booking/<int:item_id>/', views.remove_booking, name='remove_booking'),
    path('checkout_booking/', views.checkout_booking, name='checkout_booking'),
    path('booking_payments/', views.booking_payments, name='booking_payments'),
    path('booking_complete/', views.booking_complete, name='booking_complete'),
    path('record_booking/', views.record_booking, name='record_booking'),
] 