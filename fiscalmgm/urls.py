from django.contrib import admin
from django.urls import path

from . import views

app_name = 'fiscalmgm'
urlpatterns = [
    path('', views.fiscalmgm_main, name='fiscalmgm_main'),
    path('siae/<int:event_id>/', views.siae, name='siae'),
    path('ver_repo/<int:event_id>/', views.ver_repo, name='ver_repo'),
    path('user_not_allowed/', views.user_not_allowed, name='user_not_allowed'),
] 