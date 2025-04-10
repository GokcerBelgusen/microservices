# sample_microservice.py
import requests
import threading
import time
 
from flask import Flask, request, jsonify

app = Flask(__name__)
SERVICE_NAME = "user-service"
SERVICE_PORT = 5001
REGISTRY_URL = "http://localhost:5000"

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from user service!'}), 200

def register_service():
    payload = {
        'name': SERVICE_NAME,
        'address': f'http://localhost:{SERVICE_PORT}'
    }
    try:
        response = requests.post(f'{REGISTRY_URL}/register', json=payload)
        if response.status_code == 200:
            print("Successfully registered with registry")
        else:
            print(f"Registration failed: {response.text}")
    except Exception as e:
        print(f"Error registering service: {e}")

def send_heartbeat():
    while True:
        try:
            requests.post(f'{REGISTRY_URL}/heartbeat', json={'name': SERVICE_NAME})
            print("Heartbeat sent")
        except Exception as e:
            print(f"Heartbeat failed: {e}")
        time.sleep(15)  # Send heartbeat every 15 seconds

# Example client code to discover and use service
def discover_and_call_service():
    try:
        response = requests.get(f'{REGISTRY_URL}/discover/{SERVICE_NAME}')
        if response.status_code == 200:
            service_address = response.json()['address']
            service_response = requests.get(f'{service_address}/hello')
            print(f"Service response: {service_response.json()}")
        else:
            print(f"Service discovery failed: {response.text}")
    except Exception as e:
        print(f"Error in service discovery: {e}")

if __name__ == '__main__':
    # Register service on startup
    register_service()
    
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    
    # Start the service
    app.run(port=SERVICE_PORT)
    
    # Example of discovering and calling the service (you'd typically do this from another service)
    time.sleep(2)  # Wait for service to start
    discover_and_call_service()
