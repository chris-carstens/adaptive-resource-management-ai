from kubernetes import client, config
from flask import Flask, jsonify, Response
import numpy as np
from prometheus_client import start_http_server, Counter, Histogram, generate_latest
import os
import logging
import logging_loki
import time

# Configure Loki logging
logging_loki.emitter.LokiEmitter.level_tag = "level"
handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "flask-app-2"},
    version="1",
)

# Get the logger and add the Loki handler
logger = logging.getLogger("flask-app-2")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = Flask(__name__)

# Load Kubernetes configuration
config.load_incluster_config() # Just for running inside the cluster
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

@app.route('/')
def hello_world():
    return 'Hello, World 2!'

# Define metrics
MATRIX_REQUESTS = Counter('second_matrix_multiply_requests_total', 'Total second matrix multiplication requests')
MATRIX_DURATION = Histogram('second_matrix_multiply_duration_seconds', 'Time spent processing second matrix multiplication')
MATRIX_OPS = Counter('second_matrix_multiply_ops_total', 'Total number of multiplication operations')

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
            
            duration: float = time.time() - start_time
            logger.info(
                "Second matrix multiplication completed",
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

# Add metrics endpoint
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


if __name__ == '__main__':
    start_http_server(8000)  # Prometheus metrics endpoint
    app.run(host='0.0.0.0', port=5000)
