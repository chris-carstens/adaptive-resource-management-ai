from kubernetes import client, config
from flask import Flask, jsonify, Response, g
import numpy as np
from prometheus_client import start_http_server, Counter, Histogram, Gauge, generate_latest
import os
import logging
import logging_loki
import time
import time
from threading import Lock
import psutil
import numpy as np
import tensorflow as tf
import os
from tensorflow.keras.metrics import Precision, Recall, BinaryAccuracy
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import AdamW
import time

class IntermediateDataset:
    def __init__(self, data_path):
        self.data_files = sorted([f for f in os.listdir(f'{data_path}') if f.endswith('_data.npy')])
        self.label_files = sorted([f for f in os.listdir(f'{data_path}') if f.endswith('_labels.npy')])
        self.data_path = data_path
        
    def __len__(self):
        return len(self.data_files)
    
    def as_dataset(self):
        def generator():
            for data_file, label_file in zip(self.data_files, self.label_files):
                data = np.load(f'{self.data_path}/{data_file}')
                labels = np.load(f'{self.data_path}/{label_file}')
                yield data, labels
        
        return tf.data.Dataset.from_generator(
            generator,
            output_signature=(
                tf.TensorSpec(shape=(None, None, None, 256), dtype=tf.float32),
                tf.TensorSpec(shape=(None,), dtype=tf.int32)
            )
        )

def train_model_part2(base_dir=None):
    # Enable eager execution
    tf.config.run_functions_eagerly(True)
    
    save_path = '/tmp/shared'
    
    # Load the preprocessed features
    train_features = np.load(f'{save_path}/train/features.npy')
    train_labels = np.load(f'{save_path}/train/labels.npy')
    test_features = np.load(f'{save_path}/test/features.npy')
    test_labels = np.load(f'{save_path}/test/labels.npy')
    
    # Validate dataset sizes
    if len(train_features) == 0 or len(test_features) == 0:
        raise ValueError("Empty dataset detected")
    
    print(f"Dataset sizes - Train: {len(train_features)}, Test: {len(test_features)}")
    
    # Create datasets
    train_dataset = tf.data.Dataset.from_tensor_slices((train_features, train_labels)).batch(32)
    test_dataset = tf.data.Dataset.from_tensor_slices((test_features, test_labels)).batch(32)

    # Second half of the model
    model_part2 = Sequential()
    model_part2.add(Dense(32, activation='relu', input_shape=(6272,)))
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

    # Load first part timing and calculate total
    part1_timing = np.load(f'{save_path}/timing_part1.npy', allow_pickle=True).item()
    total_time = part1_timing['training_time'] + part1_timing['processing_time'] + training_time

    print(f"\nTotal timing breakdown:")
    print(f"First half training: {part1_timing['training_time']:.2f} seconds")
    print(f"Feature generation: {part1_timing['processing_time']:.2f} seconds")
    print(f"Second half training: {training_time:.2f} seconds")
    print(f"Total time: {total_time:.2f} seconds")

    # Save the final model
    model_part2.save(f'{save_path}/model_part2.keras')

    return {
        'training_time': training_time,
        'metrics': {
            'precision': pre.result().numpy(),
            'recall': re.result().numpy(),
            'accuracy': acc.result().numpy()
        },
        'history': hist.history
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

# Define metrics
MATRIX_REQUESTS = Counter('second_matrix_multiply_requests_total', 'Total second matrix multiplication requests')
MATRIX_DURATION = Histogram('second_matrix_multiply_duration_seconds', 'Time spent processing second matrix multiplication')
MATRIX_OPS = Counter('second_matrix_multiply_ops_total', 'Total number of multiplication operations')
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

@app.route('/')
def hello_world():
    return 'Hello, World 2!'

@app.route('/second-matrix-multiply', methods=['GET'])
def matrix_multiply():
    try:
        MATRIX_REQUESTS.inc()
        start_time = time.time()
        with MATRIX_DURATION.time():
            if not os.path.exists('/tmp/shared/matrix_result.npy'):
                logger.error(
                    "No saved matrix found",
                    extra={
                        "tags": {
                            "error_type": "FileNotFound"
                        }
                    }
                )
                return jsonify({
                    'message': 'No saved matrix found',
                    'status': 'error'
                }), 404
                
            saved_matrix = np.load('/tmp/shared/matrix_result.npy')
            size = saved_matrix.shape[0]
            new_matrix = np.random.rand(size, size)
            final_result = np.dot(saved_matrix, new_matrix)
            
            ops_count = size * size * size
            MATRIX_OPS.inc(ops_count)
            
            np.save('/tmp/shared/second_result.npy', final_result)
            
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
                'input_shape': saved_matrix.shape,
                'result_shape': final_result.shape,
                'result_saved': True,
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

@app.route('/train/part2', methods=['GET'])
def train_part2():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        result = train_model_part2(current_dir)
        
        # Convert NumPy types for JSON serialization
        serializable_result = convert_numpy_types(result)
        
        return jsonify({
            'status': 'success',
            'message': 'Second part training completed',
            'training_time': serializable_result['training_time'],
            'metrics': serializable_result['metrics'],
            'history': serializable_result['history']
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

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    start_http_server(8000)  # Prometheus metrics endpoint
    app.run(host='0.0.0.0', port=5000)
