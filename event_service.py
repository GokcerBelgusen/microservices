# event_service.py
import threading
import time
from confluent_kafka import Consumer, KafkaException
from flask import Flask, jsonify
import requests
import json
import logging

app = Flask(__name__)
SERVICE_NAME = "event-service"
SERVICE_PORT = 5002
REGISTRY_URL = "http://localhost:5000"
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "user-events"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# In-memory store for events (in production, use a database)
processed_events = []

# Kafka consumer configuration
kafka_config = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'event-service-group',
    'auto.offset.reset': 'earliest'
}

def start_kafka_consumer():
    """Background thread to consume Kafka messages"""
    consumer = Consumer(kafka_config)
    consumer.subscribe([KAFKA_TOPIC])
    
    logger.info(f"Starting Kafka consumer for topic {KAFKA_TOPIC}")
    
    while True:
        try:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            
            event_data = json.loads(msg.value().decode('utf-8'))
            logger.info(f"Received event: {event_data}")
            processed_events.append(event_data)
            
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
            time.sleep(1)  # Back off on error

@app.route('/events', methods=['GET'])
def get_events():
    """Return all processed events"""
    return jsonify({'events': processed_events}), 200

def register_service():
    """Register with the service registry"""
    payload = {
        'name': SERVICE_NAME,
        'address': f'http://localhost:{SERVICE_PORT}'
    }
    try:
        response = requests.post(f'{REGISTRY_URL}/register', json=payload)
        if response.status_code == 200:
            logger.info("Successfully registered with registry")
        else:
            logger.error(f"Registration failed: {response.text}")
    except Exception as e:
        logger.error(f"Error registering service: {e}")

def send_heartbeat():
    """Send periodic heartbeats to registry"""
    while True:
        try:
            requests.post(f'{REGISTRY_URL}/heartbeat', json={'name': SERVICE_NAME})
            logger.debug("Heartbeat sent")
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
        time.sleep(15)

if __name__ == '__main__':
    # Register service on startup
    register_service()
    
    # Start Kafka consumer in a background thread
    kafka_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    kafka_thread.start()
    
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    
    logger.info(f"Starting {SERVICE_NAME} on port {SERVICE_PORT}")
    app.run(port=SERVICE_PORT, threaded=True)
