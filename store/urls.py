from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.store, name='store'),
    path('<slug:section_slug>/', views.store, name='shows_by_section'),
    path('<slug:section_slug>/<slug:show_slug>/', views.show_detail, name='show_detail'),
] 
