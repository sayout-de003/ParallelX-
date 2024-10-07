# connection.py
import requests
import socket
import time
import json

SERVER_URL = ' http://127.0.0.1:8000'  # Replace with your actual server URL
DEVICE_NAME = socket.gethostname()  # Use the hostname as the device name

def send_heartbeat():
    try:
        response = requests.post(SERVER_URL, json={'device_name': DEVICE_NAME})
        response.raise_for_status()  # This will raise an exception for HTTP errors
        
        # Add debug print statements
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        # Try to parse the JSON response
        try:
            json_response = response.json()
            # Process the JSON response
        except json.JSONDecodeError as json_err:
            print(f"JSON Decode Error: {json_err}")
            print(f"Raw response: {response.text}")
    except requests.RequestException as req_err:
        print(f"Request Error: {req_err}")

if __name__ == '__main__':
    while True:
        send_heartbeat()
        time.sleep(60)  # Send a heartbeat every 60 seconds
