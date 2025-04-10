from flask import Flask, request
import requests  # Ensure this import is present

app = Flask(__name__)

REGISTRY_URL = 'http://localhost:5000'
PROTECTED_SERVICES = {'service1', 'service2', 'cache'}  # Services requiring auth

@app.route('/<service>/<path:path>', methods=['GET', 'POST'])
def route_to_service(service, path):
    services = requests.get(f'{REGISTRY_URL}/services').json()
    service_url = services.get(service)
    if not service_url:
        return "Service not found", 404
    
    # Check authorization for protected services
    if service in PROTECTED_SERVICES:
        token = request.headers.get('Authorization')
        if not token or requests.get(f'{services["auth"]}/validate', headers={'Authorization': token}).status_code != 200:
            return "Unauthorized", 401
    
    if request.method == 'GET':
        return requests.get(f'{service_url}/{path}', headers=request.headers).text
    elif request.method == 'POST':
        return requests.post(f'{service_url}/{path}', json=request.json, headers=request.headers).text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
