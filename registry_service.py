# registry_service.py
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# In-memory service registry
services = {}

@app.route('/register', methods=['POST'])
def register_service():
    data = request.get_json()
    service_name = data.get('name')
    service_address = data.get('address')
    
    if not service_name or not service_address:
        return jsonify({'error': 'Missing name or address'}), 400
    
    # Store service info with timestamp
    services[service_name] = {
        'address': service_address,
        'last_heartbeat': time.time()
    }
    return jsonify({'message': f'Service {service_name} registered successfully'}), 200

@app.route('/discover/<service_name>', methods=['GET'])
def discover_service(service_name):
    service = services.get(service_name)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    # Check if service is still alive (e.g., last heartbeat within 30 seconds)
    if time.time() - service['last_heartbeat'] > 30:
        del services[service_name]
        return jsonify({'error': 'Service expired'}), 404
        
    return jsonify({'address': service['address']}), 200

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    service_name = data.get('name')
    
    if service_name in services:
        services[service_name]['last_heartbeat'] = time.time()
        return jsonify({'message': 'Heartbeat recorded'}), 200
    return jsonify({'error': 'Service not registered'}), 404

if __name__ == '__main__':
    app.run(port=5000)
    
    # Start the service
    app.run(port=SERVICE_PORT)
    
    # Example of discovering and calling the service (you'd typically do this from another service)
    time.sleep(2)  # Wait for service to start
    discover_and_call_service()
