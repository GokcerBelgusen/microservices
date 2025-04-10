from flask import Flask, request
import requests  # Added this import

app = Flask(__name__)

GATEWAY_URL = 'http://localhost:5003'

@app.route('/message')
def get_message():
    token = request.headers.get('Authorization')
    if not token or requests.get(f'{GATEWAY_URL}/auth/validate', headers={'Authorization': token}).status_code != 200:
        return "Unauthorized", 401
    cache_response = requests.get(f'{GATEWAY_URL}/cache/message')
    if cache_response.status_code == 200:
        return cache_response.text
    msg = "Hello from Service 1!"
    requests.post(f'{GATEWAY_URL}/cache/message', json={"value": msg})
    return msg

def register():
    requests.post('http://localhost:5000/register', 
                 json={"name": "service1", "url": "http://localhost:5001"})

if __name__ == '__main__':
    register()
    app.run(host='0.0.0.0', port=5001)
