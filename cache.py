from flask import Flask, request, jsonify
import requests  # Added this import

app = Flask(__name__)

cache = {}

@app.route('/<key>', methods=['GET'])
def get_cache(key):
    value = cache.get(key)
    if value is not None:
        return value, 200
    return "Not found", 404

@app.route('/<key>', methods=['POST'])
def set_cache(key):
    data = request.json
    cache[key] = data['value']
    return jsonify({"message": "Cached"}), 201

def register():
    requests.post('http://localhost:5000/register', 
                 json={"name": "cache", "url": "http://localhost:5004"})

if __name__ == '__main__':
    register()
    app.run(host='0.0.0.0', port=5004)
