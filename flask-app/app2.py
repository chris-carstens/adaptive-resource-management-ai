import os
# Suppress TensorFlow warnings and info messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_TRT_DISABLE_CUDA_LOGGER'] = '1'

from kubernetes import client, config
from flask import Flask, jsonify, request, g
import numpy as np
import logging
import logging_loki
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import AdamW

tf.get_logger().setLevel('ERROR')

app = Flask(__name__)

# Kubernetes configuration
config.load_incluster_config()
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

# Loki logging setup
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100/loki/api/v1/push")

logging_loki.emitter.LokiEmitter.level_tag = "level"
loki_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler = logging_loki.LokiHandler(
    url=LOKI_URL,
    tags={"application": "flask-app-2"},
    version="1",
)
handler.setFormatter(loki_formatter)

# Configure loggers
logger = logging.getLogger("flask-app-2")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
flask_logger.addHandler(handler)

@app.before_request
def before_request():
    # Extract request ID from headers (sent by gateway)
    g.request_id = request.headers.get('X-Request-ID', 'unknown')
    flask_logger.info(f"ID: {g.request_id} request arrived")

@app.after_request
def after_request(response):
    flask_logger.info(
        f"ID: {g.request_id} request completed with status {response.status_code}.%"
    )
    return response

@app.route('/')
def health():
    return 'App 2 is healthy!'

@app.route('/run-fire-detector-2', methods=['POST'])
def train_part2():
    # Get data from app1's request
    data = request.get_json()
        
    if not data or not data.get('part1_completed', False):
        return jsonify({
            'status': 'error',
            'message': 'Part 1 training was not completed successfully'
        }), 400
        
    train_features = np.array(data['train_features'])[:10]
    train_labels = np.array(data['train_labels'])[:10]
    test_features = np.array(data['test_features'])[:10]
    test_labels = np.array(data['test_labels'])[:10]

    train_model_part2_from_data(
        train_features, 
        train_labels, 
        test_features, 
        test_labels,
    )

    return jsonify({
        'status': 'success',
        'message': 'Second part training completed',
    }), 200


def train_model_part2_from_data(train_features, train_labels, test_features, test_labels):
    model_part2 = Sequential()
    model_part2.add(Dense(256, activation='relu', input_shape=(train_features.shape[1],)))
    model_part2.add(Dense(1, activation='sigmoid'))

    model_part2.compile(optimizer="adam", 
                    loss=tf.keras.losses.BinaryCrossentropy(),
                    metrics=['accuracy'])

    model_part2.train_on_batch(
        train_features,
        train_labels,
    )

    model_part2.predict(test_features, verbose=0)

if __name__ == '__main__':
    # Development server only
    app.run(host='0.0.0.0', port=5000, debug=True)
