from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
#

class Device(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)  # Device type (e.g., laptop, desktop)
    available = models.BooleanField(default=False)  # Indicates if the device is ready to accept jobs
    last_seen = models.DateTimeField(auto_now=True)  # Timestamp of the last heartbeat received
    ip_address = models.GenericIPAddressField() 
     # IP address of the device
    status = models.CharField(max_length=20, choices=[
        ('AVAILABLE', 'Available'),        # Device is idle and ready for training
        ('CONNECTED', 'Connected'),        # Device is connected to the system
        ('TRAINING', 'Training'),          # Device is currently training a model
        ('OFFLINE', 'Offline')             # Device is offline or not responding
    ], default='OFFLINE')  # Default status is offline

    ram = models.FloatField()  # RAM in GB
    storage = models.FloatField()  # Storage in GB
    cpu_cores = models.IntegerField(default=0)  # Number of CPU cores
    gpu = models.BooleanField(default=False)  # Whether the device has a GPU
    gpu_details = models.CharField(max_length=100, blank=True, null=True)  # Optional details about the GPU

    subnet = models.CharField(max_length=50)  # Subnet address for verification (e.g., '192.168.1.')
    last_connected = models.DateTimeField(default=timezone.now)  # Time when the device last connected to the system
    
    

    def __str__(self):
        return f"{self.name} ({self.ip_address}) - {self.get_status_display()}"

    
    def __str__(self):
        return self.name
    
class ConnectionRequest(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.device.name} - {self.timestamp}"
    
    
class TrainingRequest(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)  # Make user nullable
    nodes = models.TextField()  # You might want to create a separate model for nodes
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request by {self.user.username} - {self.status}"
    

class TrainingJob(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')  # Could be 'RUNNING', 'COMPLETED', etc.