from django.db import models

# Create your models here.
from django.db import models

class Device(models.Model):
    USER_TYPE_CHOICES = [
        ('looking', 'Looking for device to train'),
        ('available', 'Available for training'),
    ]

    user_name = models.CharField(max_length=255)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    cpu_info = models.CharField(max_length=255)
    ram_info = models.CharField(max_length=255)
    storage_info = models.CharField(max_length=255)
    gpu_info = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user_name} - {self.user_type}"

    
class ConnectionRequest(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.device.name} - {self.timestamp}"
    
    