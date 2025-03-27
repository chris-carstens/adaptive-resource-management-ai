from kubernetes import client, config
from flask import Flask, jsonify, request, Response, g
import numpy as np
from prometheus_client import start_http_server, Counter, Histogram, Gauge, generate_latest
import os
import logging
import logging_loki
import time
from threading import Lock
import psutil
import kagglehub
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten

global dataset_path
dataset_path = kagglehub.dataset_download("alik05/forest-fire-dataset")

def ensure_directories(base_path):
    dirs = ['train', 'test']
    for dir_name in dirs:
        full_path = os.path.join(base_path, dir_name)
        os.makedirs(full_path, exist_ok=True)
    return base_path

def train_model_part1(base_dir=None):
    # First half of the model
    model_part1 = Sequential()
    model_part1.add(Conv2D(32, (3,3), 1, activation='relu', input_shape=(64,64,3)))
    model_part1.add(MaxPooling2D())
    model_part1.add(Conv2D(64, (3,3), 1, activation='relu'))
    model_part1.add(MaxPooling2D())
    model_part1.add(Conv2D(128, (3,3), 1, activation='relu'))
    model_part1.add(MaxPooling2D())
    model_part1.add(Flatten())
    model_part1.add(Dense(256, activation='relu'))

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
    train_size = int(len(Training)*.8 * 0.2) # TODO: INCREASE
    test_size = int(len(Training)*.2 * 0.2) # TODO: INCREASE
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

    # Save and process results
    save_path = '/tmp/shared'
    ensure_directories(save_path)

    model_part1.save(f'{save_path}/model_part1.keras')

    # Generate and save intermediate outputs
    def save_intermediate_outputs(dataset, output_path):
        all_features = []
        all_labels = []

        for images, labels in dataset:
            features = model_part1.predict(images)
            all_features.append(features)
            all_labels.append(labels)
        
        np.save(f'{output_path}/features.npy', np.concatenate(all_features))
        np.save(f'{output_path}/labels.npy', np.concatenate(all_labels))

    # Time the intermediate results generation
    start_time = time.time()
    save_intermediate_outputs(train, f'/{save_path}/train')
    save_intermediate_outputs(test, f'/{save_path}/test')
    processing_time = time.time() - start_time
    print(f"Feature generation time: {processing_time:.2f} seconds")

    # Save timing information
    timing_info = {
        'training_time': training_time,
        'processing_time': processing_time
    }
    np.save(f'/{save_path}/timing_part1.npy', timing_info)
    
    return {
        'training_time': training_time,
        'processing_time': processing_time,
        'history': hist.history
    }



# Configure Loki logging
logging_loki.emitter.LokiEmitter.level_tag = "level"
handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "flask-app-1"},
    version="1",
)
loki_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(loki_formatter)

# Get the logger and add the Loki handler
logger = logging.getLogger("flask-app-1")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Configure Flask logging
# Comment or uncomment to vizualize the logs from loki or from flask
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
flask_handler = logging.StreamHandler()
flask_logger.addHandler(handler)

app = Flask(__name__)

# Load Kubernetes configuration
config.load_incluster_config() # Just for running inside the cluster
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

# Create shared directories at startup
os.makedirs('/tmp/shared', exist_ok=True)
os.makedirs('/tmp/shared/train', exist_ok=True)
os.makedirs('/tmp/shared/test', exist_ok=True)

@app.route('/')
def hello_world():
    return 'Hello, World 1!'

# Define metrics
MATRIX_REQUESTS = Counter('matrix_multiply_requests_total', 'Total matrix multiplication requests')
MATRIX_DURATION = Histogram('matrix_multiply_duration_seconds', 'Time spent processing matrix multiplication')
MATRIX_OPS = Counter('matrix_multiply_ops_total', 'Total number of multiplication operations')
CPU_USAGE = Gauge('flask_app_cpu_percent', 'CPU usage percentage')

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
    cpu_percent = psutil.cpu_percent(interval=0.1)
    CPU_USAGE.set(cpu_percent)

    flask_logger.info(
        f"CPU Usage: {cpu_percent}%"
    )
    flask_logger.info(
        f"ID: {g.request_id} request completed with status {response.status_code}.%"
    )
    return response

@app.route('/matrix-multiply', methods=['GET'])
def matrix_multiply():
    try:
        MATRIX_REQUESTS.inc()
        start_time = time.time()
        with MATRIX_DURATION.time():
            size = int(request.args.get('size', 1000))
            matrix_a = np.random.rand(size, size)
            matrix_b = np.random.rand(size, size)
            result = np.dot(matrix_a, matrix_b)
            
            ops_count = size * size * size
            MATRIX_OPS.inc(ops_count)
            
            np.save('/tmp/shared/matrix_result.npy', result)
            
            duration = time.time() - start_time
            logger.info(
                "Matrix multiplication completed in {duration} seconds",
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
            'result_shape': result.shape,
            'result_saved': True,
            'operations_performed': ops_count,
            'duration_seconds': duration
        })
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
        
        return jsonify({
            'status': 'success',
            'message': 'First part training completed',
            'training_time': result['training_time'],
            'processing_time': result['processing_time'],
            'history': result['history']
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add metrics endpoint
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


if __name__ == '__main__':
    start_http_server(8000)  # Prometheus metrics endpoint
    app.run(host='0.0.0.0', port=5000)
