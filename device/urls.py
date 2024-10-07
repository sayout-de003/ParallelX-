from django.urls import path, include
from . import views
from .views import home
app_name = 'device'  # Add this line to define the namespace

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_device, name='register_device'),
    path('list/', views.device_list, name='device_list'),
    path('send_request/<int:device_id>/', views.send_request, name='send_request'),
]
