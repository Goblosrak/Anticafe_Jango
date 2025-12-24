from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('zones/', views.zones, name='zones'),
    path('booking/', views.booking, name='booking'),
    path('contacts/', views.contacts, name='contacts'),
    path('api/availability/', views.check_availability_api, name='availability_api'),
    path('debug/time/', views.debug_time_info, name='debug_time'),
    
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/history/', views.booking_history_view, name='booking_history'),
]