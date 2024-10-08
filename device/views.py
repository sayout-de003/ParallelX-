from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import psutil
import socket
import subprocess
import platform
import requests
from .models import Device, TrainingJob, ConnectionRequest, TrainingRequest
import os
from django.http import HttpResponse


# Home view
def home(request):
    return render(request, 'device/home.html')


# Helper function to gather device info
def get_device_info():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        ram = psutil.virtual_memory().total / (1024 ** 3)  # RAM in GB
        storage = psutil.disk_usage('/').total / (1024 ** 3)  # Storage in GB
        cpu_cores = psutil.cpu_count()  # CPU cores

        gpu_available = False
        gpu_details = None
        try:
            result = subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT)
            gpu_available = True
            gpu_details = result.decode('utf-8')
        except Exception:
            gpu_available = False

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


# Register device view
def register_device(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        device_type = request.POST.get('type')
        device_info = get_device_info()
        device = Device(name=name, type=device_type, **device_info)
        device.save()
        return redirect('device:device_list')
    return render(request, 'device/register_device.html')


# Device status check helper functions
def is_device_online(ip_address):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', ip_address]  # Ping once
    try:
        response = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return response.returncode == 0
    except Exception as e:
        print(f"Error checking if device is online: {e}")
        return False


def is_device_connected(device):
    return TrainingJob.objects.filter(device=device, status='RUNNING').exists()


def is_device_busy(device):
    return TrainingJob.objects.filter(device=device, status__in=['RUNNING', 'PENDING']).exists()


# Device list view
def device_list(request):
    status_filter = request.GET.get('status', None)
    devices = Device.objects.all()
    device_statuses = []

    for device in devices:
        ip_address = device.ip_address
        online_status = is_device_online(ip_address)

        if not online_status:
            status = 'OFFLINE'
        else:
            pending_request = TrainingRequest.objects.filter(nodes__contains=device.id, status='PENDING').exists()
            if pending_request:
                status = 'REQUEST_SENT'
            elif is_device_connected(device):
                status = 'CONNECTED'
            elif is_device_busy(device):
                status = 'BUSY'
            else:
                status = 'AVAILABLE'

        device_statuses.append({'device': device, 'status': status})

    if status_filter:
        device_statuses = [ds for ds in device_statuses if ds['status'] == status_filter]

    return render(request, 'device/device_list.html', {'devices': device_statuses, 'status_filter': status_filter})


# Send connection request to device
def send_connection_request(request, device_id):
    device = get_object_or_404(Device, id=device_id)

    if request.method == 'POST':
        device_ip = device.ip_address

        try:
            response = requests.post(f"http://{device_ip}:5001/notify", json={"message": "New training request"})

            if response.status_code == 200:
                nodes = request.POST.getlist('nodes')
                user = request.user if request.user.is_authenticated else None

                TrainingRequest.objects.create(user=user, nodes=','.join(nodes), status='PENDING')
                ConnectionRequest.objects.create(device=device, ip_address=device_ip, status='PENDING', created_at=now())

                return JsonResponse({'status': 'success', 'message': 'Request sent successfully', 'device_id': device_id})

            return JsonResponse({'status': 'error', 'message': 'Failed to notify the device', 'response_code': response.status_code})

        except requests.exceptions.RequestException as e:
            return JsonResponse({'status': 'error', 'message': f'Connection error: {str(e)}'})

    devices = Device.objects.all()
    return render(request, 'device/send_request.html', {'devices': devices})


# Handle connection request (accept/reject)
@csrf_exempt
def handle_connection_request(request, request_id):
    try:
        connection_request = ConnectionRequest.objects.get(id=request_id)
        sender_device = connection_request.device
        available_ides = get_available_ides()

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'accept':
                connection_request.status = 'ACCEPTED'
                connection_request.save()
                return redirect('device:choose_ide', request_id=request_id)

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


# View pending notifications
def view_notifications(request):
    pending_requests = ConnectionRequest.objects.filter(status='PENDING')
    return render(request, 'device/notification.html', {'pending_requests': pending_requests})


# Get list of available IDEs on the device
def get_available_ides():
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
    for ide, command in ide_commands.items():
        try:
            subprocess.check_output(command, shell=True)
            available_ides.append(ide)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    return available_ides


# Choose IDE for training
def choose_ide(request, request_id):
    training_request = get_object_or_404(TrainingRequest, id=request_id)
    available_ides = get_available_ides()

    if request.method == 'POST':
        selected_ide = request.POST.get('selected_ide')
        # Redirect to the start_training view with request_id and selected ide
        return redirect('device:start_training', request_id=request_id, ide=selected_ide)

    return render(request, 'device/choose_ide.html', {'ides': available_ides, 'request_id': request_id})




from django.shortcuts import render

import os
import subprocess
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from device.models import TrainingRequest

import os
import subprocess
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from .models import TrainingRequest

def start_training(request, request_id, ide):
    training_request = get_object_or_404(TrainingRequest, id=request_id)

    if request.method == 'POST':
        # Get the file path from the POST request
        file_path = request.POST.get('file_path')

        # Ensure the file path exists
        if not file_path or not os.path.exists(file_path):
            return HttpResponse("File path does not exist.", status=400)

        print(f"Starting training with nodes: {training_request.nodes} using IDE: {ide}")

        # Detect nodes (connected devices)
        nodes = training_request.nodes.split(',')  # Assuming nodes are comma-separated
        num_nodes = len(nodes)
        framework = None

        # Framework detection for Python or Jupyter notebook files
        if file_path.endswith('.py'):
            framework = detect_framework(file_path)  # Detect framework from .py script

        elif file_path.endswith('.ipynb'):
            framework = detect_framework_notebook(file_path)  # Detect framework from .ipynb

        if not framework:
            return HttpResponse("Unsupported framework. Only TensorFlow and PyTorch are supported.", status=400)

        # Build command for distributed training based on the framework
        if file_path.endswith('.py'):
            # If it's a Python script, run with the nodes argument
            command = f"python {file_path} --nodes {','.join(nodes)}"
        elif file_path.endswith('.ipynb'):
            # Handle the case for Jupyter notebook
            if ide == 'VS Code':
                # Open the notebook in VS Code
                command = f"code {file_path}"
            elif ide == 'Jupyter':
                # Open the notebook using Jupyter
                command = f"jupyter notebook {file_path}"
            else:
                return HttpResponse("Unsupported IDE for notebook files.", status=400)
        else:
            return HttpResponse("Unsupported file type. Only .py or .ipynb files are allowed.", status=400)

        try:
            # Use subprocess to run the command
            subprocess.Popen(command, shell=True)
            print(f"Command executed: {command}")
        except Exception as e:
            print(f"Error starting training: {e}")
            return HttpResponse(f"Error executing the command: {e}", status=500)

        return redirect('device:device_list')

    # Handle GET request: render the form for entering the file path
    return render(request, 'device/start_training.html', {
        'request_id': request_id,
        'ide': ide,
    })

def detect_framework(file_path):
    """Detect if the training script (.py) is PyTorch or TensorFlow based on imports."""
    with open(file_path, 'r') as f:
        content = f.read()
        if 'torch' in content:
            return 'pytorch'
        elif 'tensorflow' in content:
            return 'tensorflow'
    return None

def detect_framework_notebook(file_path):
    """Detect if the Jupyter notebook (.ipynb) uses PyTorch or TensorFlow."""
    with open(file_path, 'r') as f:
        notebook = json.load(f)
    
    # Iterate over notebook cells to find the import statements
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':  # Only check code cells
            for line in cell.get('source', []):
                if 'import torch' in line:
                    return 'pytorch'
                elif 'import tensorflow' in line:
                    return 'tensorflow'
    return None
