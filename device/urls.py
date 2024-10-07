from django.urls import path, include
from . import views
from .views import home
app_name = 'device'  # Add this line to define the namespace

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_device, name='register_device'),
    path('list/', views.device_list, name='device_list'),
    path('send_request/<int:device_id>/', views.send_connection_request, name='send_request'),
    # Handle connection request (accept/reject)
    # Fix here: use 'recipient_id' instead of 'device_id'
    path('send-request/<int:recipient_id>/', views.send_connection_request, name='send_connection_request'),

    path('handle-request/<int:request_id>/', views.handle_connection_request, name='handle_connection_request'),

    # IDE selection view
    path('choose_ide/<int:request_id>/', views.choose_ide, name='choose_ide'),
    path('notification/', views.view_notifications, name='notification_page'),


]
