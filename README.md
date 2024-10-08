

---

# Parallalx: Distributed AI/ML Training System

Parallalx is a Django-based system designed to manage distributed AI/ML model training across multiple devices. Devices in the system collaborate to share workloads, with notifications and connection requests facilitating task distribution and workload management. The project includes support for device-specific IDE selection, library installation, and asynchronous task processing.

---

## Features
- **Device Management**: Manage multiple devices that collaborate on training tasks.
- **Notification System**: Receive and handle connection requests from other devices via a Flask-based notification server.
- **IDE Selection**: Automatically detect and select available IDEs on each device.
- **Distributed Workload Processing**: Distribute and parallelize AI/ML workloads across multiple devices.
- **Customizable Architecture**: Easily extend the application for various AI/ML tasks.

---

## Project Structure

```
parallalx/
│
├── manage.py                # Django management script
├── requirements.txt         # Project dependencies
│
├── parallax/                # Project configuration directory
│   ├── __init__.py          # Package initialization
│   ├── settings.py          # Django settings
│   ├── urls.py              # Project-wide URL routing
│   ├── wsgi.py              # WSGI configuration for deployment
│   └── asgi.py              # ASGI configuration for asynchronous support
│
├── templates/               # HTML templates for the app
│   ├── base.html            # Base template
│   
├── static/                  # Static files (CSS, JS, images)
│   ├── css/                 # CSS files
│   ├── js/                  # JavaScript files
│   └── images/              # Image files
│
├── device/                  # Device-specific functionality
│   ├── templates/           # HTML templates for device-related operations
│   │   ├── device/
│   │   │   ├── start_training.html           # Start training page
│   │   │   ├── choose_ide.html               # IDE selection page for device
│   │   │   ├── notification.html             # Device-specific notification page
│   │   │   ├── handle_connection_request.html # Page to handle connection requests
│   │   └── ...
│   ├── views.py             # View functions for device-related operations
│   ├── forms.py             # Forms for user input related to devices
│   ├── urls.py              # URL routing for device-related views
│   ├── models.py            # Database models for devices
│   └── ...
│
└── notification_server.py   # Flask-based server for handling notifications
```

---

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/parallalx.git
   cd parallalx
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database**:

   Apply the migrations to set up the initial database schema.

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Run the Django development server**:

   Start the Django development server:

   ```bash
   python manage.py runserver
   ```

   By default, the application will be accessible at `http://127.0.0.1:8000/`.

5. **Run the Notification Server**:

   The `notification_server.py` script runs as a Flask server, which manages notifications and device connection requests. You can run it on a different port (e.g., 5000).

   To run the notification server:

   ```bash
   python notification_server.py
   ```

   By default, it will run on `http://127.0.0.1:5000/`. You can configure this to run on another port if needed (e.g., `http://127.0.0.1:5001/`).

---

## Workflow Overview

1. **Connection Requests**:
   - Devices send connection requests to each other via the Flask notification server.
   - The `notification_server.py` listens for requests and sends notifications.
   - The user accepts or rejects the request via the `notification.html` page in the Django app.

2. **IDE Selection**:
   - Upon accepting a connection, the user selects an IDE (via `choose_ide.html`).
   - The system automatically installs required libraries based on the selected IDE.

3. **Training Start**:
   - After selecting the IDE and setting up the environment, training is initiated from the main device.
   - The training task is distributed across connected devices, utilizing parallel processing to accelerate the model training process.

---

## How It Works: Workflow Diagram

Below is a visual representation of the project workflow. (Add your diagram here.)

---

## Device-Specific Functions

The `device/` app handles operations specific to the devices, such as:

- **Start Training** (`start_training.html`): Initiates a training task on the device.
- **IDE Selection** (`choose_ide.html`): Allows the user to select an IDE for the device.
- **Handle Connection Requests** (`handle_connection_request.html`): Lets users approve or deny device connection requests.

---

## Notification System

The notification system is managed by the `notification_server.py`, a Flask-based server running separately from the Django application. This server listens for incoming connection requests and sends notifications to users.

### Running the Notification Server:

Run the notification server in a separate terminal or background process:

```bash
python path/to/notification_server.py
```

This server will be responsible for handling and sending connection requests and notifications. It runs on a separate port (e.g., `http://127.0.0.1:5000/`) and communicates with the main Django server to manage connection requests.

---

## Writing a Distributed Training Script

Here’s how you can prepare your PyTorch or TensorFlow scripts for distributed training:

### For PyTorch:
If you are using PyTorch, ensure you use `torch.distributed` for parallelism. Here's an example of a distributed training script in PyTorch:

```python
import argparse
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nodes', type=str, help='Comma-separated list of nodes')
    args = parser.parse_args()

    # Initialize distributed training
    dist.init_process_group(backend="gloo", init_method="tcp://localhost:23456", 
                            world_size=len(args.nodes.split(',')), rank=0)

    # Define your model
    model = YourModel()
    
    # Wrap your model for distributed training
    model = DDP(model)

    # Training loop
    for epoch in range(num_epochs):
        # Implement your distributed training logic here
        ...

    # Save the model
    torch.save(model.state_dict(), 'model.pth')

if __name__ == '__main__':
    main()
```

**Key Points**:
- Use `torch.distributed` for distributed communication.
- Wrap your model using `DistributedDataParallel` for multi-device training.

### For TensorFlow:
TensorFlow handles distributed training via the `tf.distribute` API. Here’s an example of how to set it up:

```python
import tensorflow as tf

# Multi-worker distributed training
strategy = tf.distribute.MultiWorkerMirroredStrategy()

with strategy.scope():
    # Define your model
    model = tf.keras.models.Sequential([...])

    # Compile the model
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')

    # Prepare your data
    train_dataset = ...

    # Train the model
    model.fit(train_dataset, epochs=10)

# Save the model
model.save('model.h5')
```

**Key Points**:
- Use `MultiWorkerMirroredStrategy` for distributing work across multiple devices.
- Place your model and training logic inside the strategy scope.

---

## Troubleshooting

- **File path does not exist**: Ensure that the file path you provide is correct and accessible to the system.
- **Unsupported framework**: Only PyTorch and TensorFlow are currently supported. Ensure your script uses `import torch` or `import tensorflow`.

---

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss improvements.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contact

For questions or support, please contact `desayantan216@gmail.com`.

---

