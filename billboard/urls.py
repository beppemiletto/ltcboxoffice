from django.urls import path
from . import views

app_name = 'billboard'

urlpatterns = [
    # Test endpoint
    path('api/test/', views.api_test, name='api_test'),

    # Main configuration generator
    path('config-generator/', views.venue_config_generator, name='venue_config_generator'),

    # API endpoints
    path('api/generate-config/', views.generate_venue_config, name='generate_venue_config'),
    path('api/validate-config/', views.validate_venue_config, name='validate_venue_config'),
    path('api/save-config/', views.save_venue_config, name='save_venue_config'),
    path('api/load-config/<int:venue_id>/', views.load_venue_config, name='load_venue_config'),
]
