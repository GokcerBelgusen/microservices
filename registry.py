from flask import Flask, request, jsonify

app = Flask(__name__)

services = {}

@app.route('/register', methods=['POST'])
def register_service():
    data = request.json
    services[data['name']] = data['url']
    return jsonify({"message": "Registered"}), 201

@app.route('/services', methods=['GET'])
def get_services():
    return jsonify(services), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
