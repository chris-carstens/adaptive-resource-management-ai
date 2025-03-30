from kubernetes import client, config
from flask import Flask, jsonify, request, Response, g
import numpy as np
import os
import logging
import logging_loki
import time
from threading import Lock
import kagglehub
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten
import requests

global dataset_path
dataset_path = kagglehub.dataset_download("alik05/forest-fire-dataset")

def ensure_directories(base_path):
    dirs = ['train', 'test']
    for dir_name in dirs:
        full_path = os.path.join(base_path, dir_name)
        os.makedirs(full_path, exist_ok=True)
    return base_path

def train_model_part1(base_dir=None):
    model_part1 = Sequential()
    model_part1.add(Conv2D(64, (3,3), 1, activation='relu', input_shape=(64,64,3)))
    model_part1.add(MaxPooling2D())
    model_part1.add(Conv2D(32, (3,3), 1, activation='relu'))
    model_part1.add(MaxPooling2D())
    model_part1.add(Flatten())

    # Compile first model with correct metrics
    model_part1.compile(optimizer='adam', 
                       loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                       metrics=['accuracy'])

    try:
        # Download dataset using kagglehub
        # Update the training path to point to the downloaded dataset
        training_path = os.path.join(dataset_path, "Forest Fire Dataset", "Training")
        
        if not os.path.exists(training_path):
            error_msg = f"Training data not found at {training_path}"
            raise FileNotFoundError(error_msg)
            
        # Load and preprocess data
        Training = tf.keras.utils.image_dataset_from_directory(
            training_path,
            image_size=(64, 64)
        )
        Training = Training.map(lambda x,y: (x/255, y))
    except Exception as e:
        error_msg = f"Failed to load dataset: {str(e)}"
        raise Exception(error_msg)

    # Split data
    train_size = int(len(Training)*.8 * 0.5)
    test_size = int(len(Training)*.2 * 0.5)
    train = Training.take(train_size)
    test = Training.skip(train_size).take(test_size)

    # Add tensorboard callback
    logdir='logs_part1'
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)

    # Time the training of first half
    start_time = time.time()

    hist = model_part1.fit(train, 
                          epochs=1, 
                          validation_data=test, 
                          callbacks=[tensorboard_callback])

    training_time = time.time() - start_time
    print(f"First half training time: {training_time:.2f} seconds")

    # Generate intermediate outputs directly (without saving to disk)
    def generate_features(dataset):
        all_features = []
        all_labels = []

        for images, labels in dataset:
            features = model_part1.predict(images)
            all_features.append(features)
            all_labels.append(labels)
        
        return np.concatenate(all_features), np.concatenate(all_labels)

    # Time the intermediate results generation
    start_time = time.time()
    train_features, train_labels = generate_features(train)
    test_features, test_labels = generate_features(test)
    processing_time = time.time() - start_time
    print(f"Feature generation time: {processing_time:.2f} seconds")
    
    return {
        'training_time': training_time,
        'processing_time': processing_time,
        'train_features': train_features,
        'train_labels': train_labels,
        'test_features': test_features,
        'test_labels': test_labels,
        'history': hist.history
    }

# Configure Loki logging
logging_loki.emitter.LokiEmitter.level_tag = "level"
loki_handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "flask-app-1"},
    version="1",
)
loki_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
loki_handler.setFormatter(loki_formatter)

# Get the logger and add the Loki handler
logger = logging.getLogger("flask-app-1")
logger.setLevel(logging.INFO)
logger.addHandler(loki_handler)

# Configure Flask logging
# Comment or uncomment to vizualize the logs from loki or from flask
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
flask_handler = logging.StreamHandler()
flask_logger.addHandler(loki_handler)

app = Flask(__name__)

# Load Kubernetes configuration
config.load_incluster_config() # Just for running inside the cluster
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

@app.route('/')
def hello_world():
    return 'Hello, World 1!'

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

@app.route('/matrix-multiply', methods=['GET'])
def matrix_multiply():
    try:
        start_time = time.time()
        size = int(request.args.get('size', 1000))
        matrix_a = np.random.rand(size, size)
        matrix_b = np.random.rand(size, size)
        result = np.dot(matrix_a, matrix_b)
        
        ops_count = size * size * size
        
        try:
            # Convert numpy array to list for JSON serialization
            result_list = result.tolist()
            response = requests.post(
                'http://flask-app-2-service:5000/second-matrix-multiply',
                json={'matrix': result_list, 'size': size}
            )
            app2_result = response.json()
            
            duration = time.time() - start_time
            logger.info(
                f"Matrix multiplication completed in {duration} seconds",
                extra={
                    "tags": {
                        "matrix_size": size,
                        "ops_count": ops_count,
                        "duration_seconds": duration
                    }
                }
            )
            
            return jsonify({
                'message': 'Matrix multiplication successful',
                'status': 'success',
                'initial_result_shape': list(result.shape),
                'app2_result': app2_result,
                'operations_performed': ops_count,
                'duration_seconds': duration
            })
            
        except requests.RequestException as e:
            logger.error(f"Failed to communicate with app2: {str(e)}")
            return jsonify({
                'message': f'Failed to communicate with app2: {str(e)}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logger.error(
            f"Matrix multiplication failed: {str(e)}",
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

@app.route('/train/part1', methods=['GET'])
def train_part1():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        result = train_model_part1(current_dir)
        
        # Prepare data to send to app2 (directly from memory, not from disk)
        try:
            # Convert arrays to lists for JSON serialization
            payload = {
                'part1_completed': True,
                'part1_training_time': float(result['training_time']),
                'part1_processing_time': float(result['processing_time']),
                'train_features': result['train_features'].tolist(),
                'train_labels': result['train_labels'].tolist(),
                'test_features': result['test_features'].tolist(),
                'test_labels': result['test_labels'].tolist()
            }
            
            # Make POST request to app2
            response = requests.post(
                'http://flask-app-2-service:5000/train/part2',
                json=payload
            )
            app2_result = response.json()
        
            
            # Combine results from both parts
            return jsonify({
                'status': 'success',
                'message': 'Full training pipeline completed',
                'part1': {
                    'training_time': result['training_time'],
                    'processing_time': result['processing_time'],
                },
                'part2': app2_result
            }), 200
            
        except Exception as e:
            logger.error(f"Error preparing or sending data to app2: {str(e)}")
            return jsonify({
                'status': 'partial_success',
                'message': f'First part training completed but error in data transfer: {str(e)}',
                'training_time': result['training_time'],
                'processing_time': result['processing_time'],
            }), 200

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
