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
        device_id = device.id
        device.save()
        return redirect('device_list')
    return render(request, 'device/register_device.html')
    


from django.shortcuts import render
from .models import Device

from django.shortcuts import render
from .models import Device, TrainingJob

from django.shortcuts import render, redirect, get_object_or_404
from .models import Device, TrainingJob, TrainingRequest

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
            # Check if there are any pending training requests for the device
            pending_request = TrainingRequest.objects.filter(nodes__contains=device.id, status='PENDING').exists()

            if pending_request:
                status = 'REQUEST_SENT'  # Show that a request is sent but not yet accepted
            elif is_device_connected(device):
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


from django.http import JsonResponse
import requests  # For sending HTTP requests to the device
from .models import Device, TrainingRequest

# views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Device, ConnectionRequest
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Device, TrainingRequest
import requests

def send_connection_request(request, device_id):
    device = get_object_or_404(Device, id=device_id)  # Better way to handle missing device

    if request.method == 'POST':
        device_ip = device.ip_address

        try:
            # Send a pop-up notification to the device via its IP
            response = requests.post(f"http://{device_ip}:5001/notify", json={"message": "New training request"})

            if response.status_code == 200:
                nodes = request.POST.getlist('nodes')
                user = request.user if request.user.is_authenticated else None

                # Create a TrainingRequest instance
                training_request = TrainingRequest.objects.create(user=user, nodes=','.join(nodes), status='PENDING')

                # Create a ConnectionRequest instance
                connection_request = ConnectionRequest.objects.create(
                    device=device,
                    ip_address=device_ip,
                    status='PENDING',
                    created_at=now()  # Ensure created_at is set
                )

                return JsonResponse({'status': 'success', 'message': 'Request sent successfully', 'device_id': device_id})

            return JsonResponse({'status': 'error', 'message': 'Failed to notify the device', 'response_code': response.status_code})

        except requests.exceptions.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Connection error: {str(e)}'})

    devices = Device.objects.all()
    return render(request, 'device/send_request.html', {'devices': devices})


# views.py


from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import subprocess

@csrf_exempt
@csrf_exempt
def handle_connection_request(request, request_id):
    try:
        connection_request = ConnectionRequest.objects.get(id=request_id)

        # Get the sender device (assuming you have sender in your ConnectionRequest model)
        sender_device = connection_request.device
        available_ides = get_available_ides()  # Make sure this function is implemented

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'accept':
                connection_request.status = 'ACCEPTED'
                connection_request.save()
                return redirect('device:choose_ide', request_id=request_id)  # Redirect to choose IDE

            elif action == 'reject':
                connection_request.status = 'REJECTED'
                connection_request.save()
                return JsonResponse({'status': 'rejected', 'message': 'Request rejected successfully.'})

        return render(request, 'device/handle_connection_request.html', {
            'connection_request': connection_request,
            'available_ides': available_ides,
            'sender_ip': sender_device.ip_address
        })

    except ConnectionRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Connection request not found.'}, status=404)


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


from django.shortcuts import render
from .models import TrainingRequest

def view_notifications(request):
    pending_requests = ConnectionRequest.objects.filter(status='PENDING')
    
    for req in pending_requests:
        print(f"Request ID: {req.id}, Sender: {req.sender}")

    return render(request, 'device/notification.html', {
        'pending_requests': pending_requests
    })


import os
import subprocess

def get_available_ides():
    # List of common IDEs and their detection commands/executables
    ide_commands = {
        'VS Code': 'code --version',
        'PyCharm': 'pycharm --version',
        'Jupyter': 'jupyter --version',
        'Atom': 'atom --version',
        'Sublime Text': 'subl --version',
        'Spyder': 'spyder --version',
        'Eclipse': 'eclipse -version',
        'IntelliJ IDEA': 'idea --version',
        'NetBeans': 'netbeans --version',
        'Anaconda': 'anaconda --version',
        'Cursor': 'cursor --version',

    }

    available_ides = []

    # Check each IDE
    for ide, command in ide_commands.items():
        try:
            # Run command to check if IDE is available
            subprocess.check_output(command, shell=True)
            available_ides.append(ide)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If command fails or is not found, IDE is not installed
            pass

    return available_ides

def choose_ide(request, request_id):
    training_request = TrainingRequest.objects.get(id=request_id)
    available_ides = get_available_ides()

    if request.method == 'POST':
        selected_ide = request.POST.get('selected_ide')
        # Redirect to start training
        return redirect('start_training', request_id=request_id, ide=selected_ide)

    return render(request, 'device/choose_ide.html', {
        'ides': available_ides,
        'request_id': request_id
    })
