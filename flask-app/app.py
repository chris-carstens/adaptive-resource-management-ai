from kubernetes import client, config
from flask import Flask, jsonify, request, Response
import numpy as np
from prometheus_client import start_http_server, Counter, Histogram, generate_latest
import os
import logging
import logging_loki
import time  # Add this import at the top

# Configure Loki logging
logging_loki.emitter.LokiEmitter.level_tag = "level"
handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "flask-app-1"},
    version="1",
)

# Get the logger and add the Loki handler
logger = logging.getLogger("flask-app-1")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = Flask(__name__)

# Load Kubernetes configuration
config.load_incluster_config() # Just for running inside the cluster
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

# Create a directory for shared data
os.makedirs('/tmp/shared', exist_ok=True)

@app.route('/')
def hello_world():
    return 'Hello, World 1!'

@app.route('/scale', methods=['POST'])
def scale_deployment():
    try:
        replicas = request.json.get('replicas', 1)
        
        deployment = apps_v1.read_namespaced_deployment(
            name='flask-app',
            namespace='default'
        )
        deployment.spec.replicas = replicas
        apps_v1.patch_namespaced_deployment(
            name='flask-app',
            namespace='default',
            body=deployment
        )
        
        return jsonify({
            'message': f'Deployment scaled to {replicas} replicas',
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'message': str(e),
            'status': 'error'
        }), 500

@app.route('/deployment', methods=['GET'])
def get_deployment():
    try:
        deployment = apps_v1.read_namespaced_deployment(
            name='flask-app',
            namespace='default'
        )
        
        return jsonify({
            'replicas': deployment.spec.replicas,
            'available_replicas': deployment.status.available_replicas,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'message': str(e),
            'status': 'error'
        }), 500

# Define metrics
MATRIX_REQUESTS = Counter('matrix_multiply_requests_total', 'Total matrix multiplication requests')
MATRIX_DURATION = Histogram('matrix_multiply_duration_seconds', 'Time spent processing matrix multiplication')
MATRIX_OPS = Counter('matrix_multiply_ops_total', 'Total number of multiplication operations')
# MATRIX_OPS_RATE = Histogram('matrix_multiply_ops_per_second', 'Number of matrix operations per second')

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
            # Add Loki logging
            logger.info(
                "Matrix multiplication completed",
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

# Add metrics endpoint
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


if __name__ == '__main__':
    start_http_server(8000)  # Prometheus metrics endpoint
    app.run(host='0.0.0.0', port=5000)
