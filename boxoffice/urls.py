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
    path('boxoffice_print/<int:event_id>/<int:method_id>/', views.boxoffice_print, name='boxoffice_print'),
    path('close_transaction/<int:event_id>/', views.close_transaction, name='close_transaction'),
    path('change_bookings/<int:event_id>/', views.change_bookings, name='change_bookings'),
    path('edit_order/<int:order_id>/', views.edit_order, name='edit_order'),
    path('obliterate/<str:ticket_number>/', views.obliterate, name='obliterate'),
    path('erase_order/<int:userorder_id>/<int:order_id>/', views.erase_order, name='erase_order'),
    path('sell_booking/<int:order>/', views.sell_booking, name='sell_booking'),
    path('event_list/', views.event_list, name='event_list'),
] 