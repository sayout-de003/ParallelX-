from django.shortcuts import render, redirect
from .models import Device, TrainingJob
from setuptools import dist
import psutil
import socket
import GPUtil
from django.utils import timezone # Create your views here.
# views.py
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt




def home(request):
    return render(request, 'device/home.html')


import socket
import psutil  # Make sure to install this package
import subprocess

def get_device_info():
    try:
        # Get the hostname of the local machine
        hostname = socket.gethostname()

        # Get the local IP address using the hostname
        ip_address = socket.gethostbyname(hostname)

        # Get the RAM size in GB
        ram = psutil.virtual_memory().total / (1024 ** 3)  # Convert bytes to GB

        # Get the storage size in GB
        storage = psutil.disk_usage('/').total / (1024 ** 3)  # Convert bytes to GB

        # Get the number of CPU cores
        cpu_cores = psutil.cpu_count()  # Returns the number of CPU cores

        # Check for GPU availability (This is a simple implementation)
        gpu_available = False
        gpu_details = None

        # Example method to check for GPU (Linux/Windows)
        try:
            result = subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT)
            gpu_available = True
            gpu_details = result.decode('utf-8')
        except Exception as e:
            gpu_available = False
            gpu_details = None

        # Get the subnet (for verification)
        subnet = '.'.join(ip_address.split('.')[:-1]) + '.'

        return {
            'ip_address': ip_address,
            'ram': ram,
            'storage': storage,
            'cpu_cores': cpu_cores,
            'gpu': gpu_available,
            'gpu_details': gpu_details,
            'subnet': subnet
        }
    except Exception as e:
        print(f"Error retrieving device info: {e}")
        return e



def register_device(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        device_type = request.POST.get('type')
        device_info = get_device_info()
        device = Device(name=name, type=device_type, **device_info)
        device.save()
        return redirect('device_list')
    return render(request, 'device/register_device.html')
    


from django.shortcuts import render
from .models import Device

from django.shortcuts import render
from .models import Device, TrainingJob

def device_list(request):
    status_filter = request.GET.get('status', None)

    # Retrieve all devices from the database
    devices = Device.objects.all()

    # Create a list to hold the device status information
    device_statuses = []

    for device in devices:
        # Get the current IP address of the device
        ip_address = device.ip_address

        # Check if the device is online
        online_status = is_device_online(ip_address)

        if not online_status:
            status = 'OFFLINE'  # Device is not reachable
        else:
            # Check if the device is connected or busy
            if is_device_connected(device):
                status = 'CONNECTED'  # Device is connected for training
            elif is_device_busy(device):
                status = 'BUSY'  # Device is busy with a training job
            else:
                status = 'AVAILABLE'  # Device is available for training

        # Add the device and its status to the list
        device_statuses.append({
            'device': device,
            'status': status,
        })

    # If there's a status filter, filter the devices accordingly
    if status_filter:
        device_statuses = [ds for ds in device_statuses if ds['status'] == status_filter]

    # Pass the list of device statuses to the template
    return render(request, 'device/device_list.html', {
        'devices': device_statuses,
        'status_filter': status_filter,
    })

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import TrainingRequest
from django.contrib.auth.decorators import login_required


def send_request(request,device_id ):
    # Retrieve available devices
    devices = Device.objects.all()  # or apply any necessary filters

    if request.method == 'POST':
        nodes = request.POST.getlist('nodes')  # Use getlist to handle multiple selections
        # Create a training request with selected nodes
        user = request.user if request.user.is_authenticated else None  # Set to None or a default user
        training_request = TrainingRequest.objects.create(user=user, nodes=','.join(nodes))
        return redirect('device:device_list')  # Use the namespaced URL name

    return render(request, 'device/send_request.html', {
        'devices': devices,  # Pass available devices to the template
    })

# Render a form to send request


def request_handle(request):
    requests = TrainingRequest.objects.filter(status='PENDING')

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        training_request = get_object_or_404(TrainingRequest, id=request_id)

        if action == 'accept':
            training_request.status = 'ACCEPTED'
            training_request.save()
            start_training(training_request)  # Call a function to start the training
        elif action == 'reject':
            training_request.status = 'REJECTED'
            training_request.save()

        return redirect('device:request_handle')  # Redirect after handling the request

    return render(request, 'device/request_handle.html', {'requests': requests})

def start_training(training_request):
    # Logic to start training with the specified nodes
    # You could integrate with your existing training framework here
    print(f"Starting training with nodes: {training_request.nodes}")
    # Add your training initiation logic here



import subprocess
import platform

def is_device_online(ip_address):
    """ Check if the device is reachable via ping. """
    # Determine the ping command and options based on the OS
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Prepare the command
    command = ['ping', param, '1', ip_address]  # Ping once

    try:
        # Execute the command
        response = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check if the command was successful (0 means reachable)
        return response.returncode == 0
    except Exception as e:
        print(f"Error checking if device is online: {e}")
        return False

def is_device_connected(device):
    # Check if there are any active training jobs associated with this device
    return TrainingJob.objects.filter(device=device, status='RUNNING').exists()

def is_device_busy(device):
    # Check if there are any training jobs associated with this device that are still running
    return TrainingJob.objects.filter(device=device, status__in=['RUNNING', 'PENDING']).exists()
