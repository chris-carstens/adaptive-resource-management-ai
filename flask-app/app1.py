from kubernetes import client, config
from flask import Flask, jsonify, g
import numpy as np
import os
import logging
import logging_loki
from threading import Lock
import kagglehub
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten


app = Flask(__name__)

global dataset_path
dataset_path = kagglehub.dataset_download("alik05/forest-fire-dataset")

# Load Kubernetes configuration
config.load_incluster_config()
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

# Configure Loki logging
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100/loki/api/v1/push")

logging_loki.emitter.LokiEmitter.level_tag = "level"
loki_handler = logging_loki.LokiHandler(
    url=LOKI_URL,
    tags={"application": "flask-app-1"},
    version="1",
)
loki_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("flask-app-1")
logger.setLevel(logging.INFO)
logger.addHandler(loki_handler)

flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
flask_logger.addHandler(loki_handler)

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
def health():
    return 'App 1 is healthy!'

@app.route('/run-fire-detector-1', methods=['POST'])
def train_part1():
    result = train_model_part1()

    response = {
        'part1_completed': True,
        'train_features': result['train_features'].tolist(),
        'train_labels': result['train_labels'].tolist(),
        'test_features': result['test_features'].tolist(),
        'test_labels': result['test_labels'].tolist()
    }

    return jsonify(response), 200

def train_model_part1():
    model_part1 = Sequential()
    model_part1.add(Conv2D(64, (3,3), 1, activation='relu', input_shape=(64,64,3)))
    model_part1.add(MaxPooling2D())
    model_part1.add(Conv2D(32, (3,3), 1, activation='relu'))
    model_part1.add(MaxPooling2D())
    model_part1.add(Flatten())

    model_part1.compile(optimizer='adam', 
                       loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                       metrics=['accuracy'])

    try:
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

    train_size = int(len(Training)*.8)
    test_size = int(len(Training)*.2)
    train = Training.take(train_size)
    test = Training.skip(train_size).take(test_size)

    # Add tensorboard callback
    logdir='logs_part1'
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)

    hist = model_part1.fit(train,
                          epochs=1,
                          validation_data=test, 
                          callbacks=[tensorboard_callback])

    def generate_features(dataset):
        all_features = []
        all_labels = []

        for images, labels in dataset:
            features = model_part1.predict(images)
            all_features.append(features)
            all_labels.append(labels)
        
        return np.concatenate(all_features), np.concatenate(all_labels)

    train_features, train_labels = generate_features(train)
    test_features, test_labels = generate_features(test)
    
    return {
        'train_features': train_features,
        'train_labels': train_labels,
        'test_features': test_features,
        'test_labels': test_labels,
        'history': hist.history
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
