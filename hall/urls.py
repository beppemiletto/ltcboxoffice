from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.hall, name='hall'),
    path('<slug:event_slug>/', views.hall_detail, name='hall_detail'),
] 
