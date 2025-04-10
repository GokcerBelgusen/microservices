from flask import Flask, request
import requests  # Added this import

app = Flask(__name__)

GATEWAY_URL = 'http://localhost:5003'

@app.route('/')
def call_service1():
    token = request.headers.get('Authorization')
    if not token or requests.get(f'{GATEWAY_URL}/auth/validate', headers={'Authorization': token}).status_code != 200:
        return "Unauthorized", 401
    return requests.get(f'{GATEWAY_URL}/service1/message', headers={'Authorization': token}).text

def register():
    requests.post('http://localhost:5000/register', 
                 json={"name": "service2", "url": "http://localhost:5002"})

if __name__ == '__main__':
    register()
    app.run(host='0.0.0.0', port=5002)
