from kubernetes import client, config
from flask import Flask, jsonify, request, Response, g
import numpy as np
import os
import logging
import logging_loki
import time
from threading import Lock
import tensorflow as tf
from tensorflow.keras.metrics import Precision, Recall, BinaryAccuracy
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import AdamW


def train_model_part2_from_data(train_features, train_labels, test_features, test_labels, part1_data=None):
    """Train the second part of the model using data received directly from app1."""
    # Enable eager execution
    tf.config.run_functions_eagerly(True)
    
    # Validate dataset sizes
    if len(train_features) == 0 or len(test_features) == 0:
        raise ValueError("Empty dataset detected")
    
    print(f"Dataset sizes - Train: {len(train_features)}, Test: {len(test_features)}")
    
    # Create datasets
    train_dataset = tf.data.Dataset.from_tensor_slices((train_features, train_labels)).batch(32)
    test_dataset = tf.data.Dataset.from_tensor_slices((test_features, test_labels)).batch(32)

    # Second half of the model
    model_part2 = Sequential()
    model_part2.add(Dense(32, activation='relu', input_shape=(train_features.shape[1],)))
    model_part2.add(Dense(1, activation='sigmoid'))

    # Compile model with correct loss
    learning_rate = 0.001
    optimizer = AdamW(learning_rate=learning_rate)
    model_part2.compile(optimizer=optimizer, 
                    loss=tf.keras.losses.BinaryCrossentropy(),
                    metrics=['accuracy'],
                    run_eagerly=True)

    # Validate datasets are not empty
    for x, y in train_dataset.take(1):
        print(f"First batch shapes - Features: {x.shape}, Labels: {y.shape}")

    # Add tensorboard callback
    logdir='logs_part2'
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)

    # Time the second half training
    start_time = time.time()

    hist = model_part2.fit(
        train_dataset,
        epochs=1,
        validation_data=test_dataset,
        callbacks=[tensorboard_callback]
    )

    training_time = time.time() - start_time
    print(f"Second half training time: {training_time:.2f} seconds")

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

    print(f"\nModel Metrics:")
    print(f"Precision: {pre.result().numpy():.4f}")
    print(f"Recall: {re.result().numpy():.4f}")
    print(f"Accuracy: {acc.result().numpy():.4f}")

    # Calculate total time including part1 if available
    total_time = training_time
    if part1_data:
        total_time += part1_data.get('part1_training_time', 0) + part1_data.get('part1_processing_time', 0)
        print(f"\nTotal timing breakdown:")
        print(f"First half training: {part1_data.get('part1_training_time', 0):.2f} seconds")
        print(f"Feature generation: {part1_data.get('part1_processing_time', 0):.2f} seconds")
        print(f"Second half training: {training_time:.2f} seconds")
        print(f"Total time: {total_time:.2f} seconds")

    return {
        'training_time': training_time,
        'metrics': {
            'precision': pre.result().numpy(),
            'recall': re.result().numpy(),
            'accuracy': acc.result().numpy()
        },
        'history': hist.history,
        'total_pipeline_time': total_time
    }

# Configure Loki logging
logging_loki.emitter.LokiEmitter.level_tag = "level"
handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "flask-app-2"},
    version="1",
)
loki_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(loki_formatter)

# Get the logger and add the Loki handler
logger = logging.getLogger("flask-app-2")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Configure Flask logging
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
flask_handler = logging.StreamHandler()
flask_logger.addHandler(handler)

app = Flask(__name__)

# Load Kubernetes configuration
config.load_incluster_config()
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

# Global counter and lock for incremental IDs
request_counter = 0
counter_lock = Lock()

@app.before_request
def before_request():
    global request_counter
    with counter_lock:
        request_counter += 1
        g.request_id = request_counter
    flask_logger.info(f"ID: {g.request_id} request arrived")

@app.after_request
def after_request(response):
    flask_logger.info(
        f"ID: {g.request_id} request completed with status {response.status_code}.%"
    )
    return response

@app.route('/')
def hello_world():
    return 'Hello, World 2!'

@app.route('/second-matrix-multiply', methods=['POST'])
def matrix_multiply():
    try:
        start_time = time.time()
        
        # Get matrix data from request
        data = request.get_json()
        if not data or 'matrix' not in data:
            return jsonify({
                'message': 'No matrix data provided',
                'status': 'error'
            }), 400
            
        # Convert received list back to numpy array
        saved_matrix = np.array(data['matrix'])
        size = saved_matrix.shape[0]
        new_matrix = np.random.rand(size, size)
        final_result = np.dot(saved_matrix, new_matrix)
        
        ops_count = size * size * size
        
        # Only save shape for response, not full array
        result_shape = final_result.shape
        
        duration = time.time() - start_time
        logger.info(
            f"Second matrix multiplication completed in {duration} seconds",
            extra={
                "tags": {
                    "matrix_size": size,
                    "ops_count": ops_count,
                    "duration_seconds": duration
                }
            }
        )

        return jsonify({
            'message': 'Second matrix multiplication successful',
            'status': 'success',
            'input_shape': list(saved_matrix.shape),
            'result_shape': list(result_shape),
            'operations_performed': ops_count,
            'duration_seconds': duration
        })
    except Exception as e:
        logger.error(
            f"Second matrix multiplication failed: {str(e)}",
            extra={
                "tags": {
                    "error_type": type(e).__name__
                }
            }
        )
        return jsonify({
            'message': str(e),
            'status': 'error'
        }), 500

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

@app.route('/train/part2', methods=['POST'])
def train_part2():
    try:
        # Get data from app1's POST request
        data = request.get_json()
        
        # Check if part1 was completed successfully
        if not data or not data.get('part1_completed', False):
            return jsonify({
                'status': 'error',
                'message': 'Part 1 training was not completed successfully'
            }), 400
        
        # Extract feature arrays from JSON
        try:
            train_features = np.array(data['train_features'])
            train_labels = np.array(data['train_labels'])
            test_features = np.array(data['test_features'])
            test_labels = np.array(data['test_labels'])

            
            # Run the model training with the received data
            part1_data = {
                'part1_training_time': data.get('part1_training_time', 0),
                'part1_processing_time': data.get('part1_processing_time', 0)
            }
            
            result = train_model_part2_from_data(
                train_features, 
                train_labels, 
                test_features, 
                test_labels,
                part1_data
            )
            
            # Convert NumPy types for JSON serialization
            serializable_result = convert_numpy_types(result)
            
            
            return jsonify({
                'status': 'success',
                'message': 'Second part training completed',
                'training_time': serializable_result['training_time'],
                'metrics': serializable_result['metrics'],
                'history': serializable_result['history'],
                'total_pipeline_time': serializable_result['total_pipeline_time']
            }), 200
            
        except KeyError as e:
            return jsonify({
                'status': 'error',
                'message': f'Missing required data field: {str(e)}'
            }), 400
            
    except Exception as e:
        logger.error(
            f"Model training failed: {str(e)}",
            extra={
                "tags": {
                    "error_type": type(e).__name__
                }
            }
        )
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
