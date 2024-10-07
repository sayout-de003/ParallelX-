from django.shortcuts import render, redirect
from .models import Device
import distutils
# Create your views here.
def home(request):
    return render(request, 'device/home.html')
import psutil
import socket
import GPUtil
from django.utils import timezone

def get_device_info():
    # Get system RAM
    ram = round(psutil.virtual_memory().total / (1024 ** 3), 2)  # Convert bytes to GB
    
    # Get available storage
    storage = round(psutil.disk_usage('/').total / (1024 ** 3), 2)  # Convert bytes to GB
    
    # Get CPU cores
    cpu_cores = psutil.cpu_count(logical=False)  # Physical cores
    
    # GPU detection using GPUtil
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu_available = True
        gpu_details = ', '.join([gpu.name for gpu in gpus])  # Concatenate GPU names if multiple GPUs are present
    else:
        gpu_available = False
        gpu_details = None
    
    # Fetch machine's IP address
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    
    # Return all device info
    return {
        'ram': ram,
        'storage': storage,
        'cpu_cores': cpu_cores,
        'gpu_available': gpu_available,
        'gpu_details': gpu_details,
        'ip_address': ip_address,
        'subnet': '.'.join(ip_address.split('.')[:3]),  # Example: '192.168.1.'
    }


def register_device(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        device_type = request.POST.get('type')
        device_info = get_device_info()
        device = Device(name=name, type=device_type, **device_info)
        device.save()
        return redirect('device_list')
    return render(request, 'device/register_device.html')
    


def list_of_available_devices():
    return []  # Placeholder empty list

def connection_request():
    pass
def request_handle():
    pass