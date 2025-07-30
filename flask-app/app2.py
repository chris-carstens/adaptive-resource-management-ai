from kubernetes import client, config
from flask import Flask, jsonify, request, g
import numpy as np
import logging
import logging_loki
import tensorflow as tf
from tensorflow.keras.metrics import Precision, Recall, BinaryAccuracy
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import AdamW
import os


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
        
    train_features = np.array(data['train_features'])
    train_labels = np.array(data['train_labels'])
    test_features = np.array(data['test_features'])
    test_labels = np.array(data['test_labels'])
            
    # Run the model training with the received data
    result = train_model_part2_from_data(
        train_features, 
        train_labels, 
        test_features, 
        test_labels,
    )

    # Convert NumPy types for JSON serialization
    serializable_result = convert_numpy_types(result)

    return jsonify({
        'status': 'success',
        'message': 'Second part training completed',
        'metrics': serializable_result['metrics'],
    }), 200


def train_model_part2_from_data(train_features, train_labels, test_features, test_labels):
    """Train the second part of the model using data received directly from app1."""
    # Enable eager execution
    tf.config.run_functions_eagerly(True)

    # Create datasets
    train_dataset = tf.data.Dataset.from_tensor_slices((train_features, train_labels)).batch(32)
    test_dataset = tf.data.Dataset.from_tensor_slices((test_features, test_labels)).batch(32)

    # Second half of the model
    model_part2 = Sequential()
    model_part2.add(Dense(8, activation='relu', input_shape=(train_features.shape[1],)))
    model_part2.add(Dense(1, activation='sigmoid'))

    # Compile model
    learning_rate = 0.01
    optimizer = AdamW(learning_rate=learning_rate)
    model_part2.compile(optimizer=optimizer, 
                    loss=tf.keras.losses.BinaryCrossentropy(),
                    metrics=['accuracy'],
                    run_eagerly=True)

    # Add tensorboard callback
    logdir='logs_part2'
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)

    hist = model_part2.fit(
        train_dataset,
        epochs=1,
        validation_data=test_dataset,
        callbacks=[tensorboard_callback]
    )

    # Initialize metrics
    pre = Precision()
    re = Recall()
    acc = BinaryAccuracy()

    # Evaluate metrics on test dataset
    for features, labels in test_dataset:
        predictions = model_part2.predict(features)
        pre.update_state(labels, predictions)
        re.update_state(labels, predictions)
        acc.update_state(labels, predictions)

    return {
        'metrics': {
            'precision': pre.result().numpy(),
            'recall': re.result().numpy(),
            'accuracy': acc.result().numpy()
        },
    }

def convert_numpy_types(obj):
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    return obj

if __name__ == '__main__':
    # Development server only
    app.run(host='0.0.0.0', port=5000, debug=True)
