from flask import Flask, request, jsonify
import requests  # Added this import

app = Flask(__name__)

valid_tokens = set()

@app.route('/token', methods=['GET'])
def issue_token():
    token = "simple-token-" + str(len(valid_tokens))
    valid_tokens.add(token)
    return jsonify({"token": token}), 200

@app.route('/validate', methods=['GET'])
def validate_token():
    token = request.headers.get('Authorization')
    if token in valid_tokens:
        return "Valid", 200
    return "Invalid", 401

def register():
    requests.post('http://localhost:5000/register', 
                 json={"name": "auth", "url": "http://localhost:5005"})

if __name__ == '__main__':
    register()
    app.run(host='0.0.0.0', port=5005)
