# api_gateway.py
import requests
from flask import Flask, request, jsonify
from functools import wraps
from time import time
from collections import defaultdict
import logging
import threading

app = Flask(__name__)
REGISTRY_URL = "http://localhost:5000"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

service_cache = {}
cache_timestamps = {}
CACHE_TTL = 30
request_counts = defaultdict(list)
RATE_LIMIT = 100
cache_lock = threading.Lock()

def get_service_address(service_name):
    current_time = time()
    with cache_lock:
        if (service_name in service_cache and 
            service_name in cache_timestamps and 
            current_time - cache_timestamps[service_name] < CACHE_TTL):
            logger.debug(f"Cache hit for {service_name}: {service_cache[service_name]}")
            return service_cache[service_name]
    
    try:
        response = requests.get(f'{REGISTRY_URL}/discover/{service_name}', timeout=2)
        if response.status_code == 200:
            address = response.json()['address']
            with cache_lock:
                service_cache[service_name] = address
                cache_timestamps[service_name] = current_time
            logger.info(f"Discovered {service_name} at {address}")
            return address
        else:
            logger.warning(f"Service {service_name} not found in registry: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error discovering {service_name}: {e}")
        return None

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time()
        request_counts[client_ip] = [t for t in request_counts[client_ip] 
                                   if current_time - t < 60]
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        request_counts[client_ip].append(current_time)
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != 'Bearer secret-token':
            logger.warning(f"Unauthorized request from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_service(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        service_name = kwargs.get('service_name')
        path = kwargs.get('path')
        service_address = get_service_address(service_name)
        
        if not service_address:
            logger.error(f"Service {service_name} not available")
            return jsonify({'error': f'Service {service_name} not available'}), 503
        
        try:
            method = request.method.lower()
            url = f"{service_address}/{path}"
            logger.info(f"Routing {method.upper()} request to {url}")
            
            headers = {k: v for k, v in request.headers.items() 
                      if k.lower() not in ['host', 'content-length']}
            
            if method == 'get':
                response = requests.get(url, headers=headers, timeout=5)
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Raw response: {response.text}")
                return response.text, response.status_code, {'Content-Type': 'application/json'}
            elif method == 'post':
                response = requests.post(url, json=request.get_json(), headers=headers, timeout=5)
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Raw response: {response.text}")
                return response.text, response.status_code, {'Content-Type': 'application/json'}
            else:
                return jsonify({'error': 'Method not supported'}), 405
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling {service_name}")
            return jsonify({'error': f'Service {service_name} timeout'}), 504
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling {service_name}: {e}")
            return jsonify({'error': f'Service error: {str(e)}'}), 502
            
    return decorated_function

@app.route('/api/<service_name>/<path:path>', methods=['GET', 'POST'])
@rate_limit
@require_auth
@require_service
def route_to_service(service_name, path):
    pass

@app.route('/health', methods=['GET'])
def health_check():
    registry_status = requests.get(f'{REGISTRY_URL}/discover/user-service').status_code == 200
    status = 'healthy' if registry_status else 'unhealthy'
    logger.info(f"Health check: {status}")
    return jsonify({'status': status}), 200 if registry_status else 503

@app.route('/', methods=['GET'])
def welcome():
    return jsonify({'message': 'Welcome to the API Gateway'}), 200

def clear_expired_cache():
    while True:
        current_time = time()
        with cache_lock:
            expired = [k for k, t in cache_timestamps.items() if current_time - t > CACHE_TTL]
            for key in expired:
                service_cache.pop(key, None)
                cache_timestamps.pop(key, None)
                logger.debug(f"Cleared expired cache for {key}")
        time.sleep(10)

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=clear_expired_cache, daemon=True)
    cleanup_thread.start()
    logger.info("Starting API Gateway on port 8080")
    app.run(host='0.0.0.0', port=8080, threaded=True)
