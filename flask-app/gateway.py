from flask import Flask, jsonify, request, g
import requests
import os
from kubernetes import client, config
import logging
import logging_loki
import time
from threading import Lock

app = Flask(__name__)

# Loki logging setup
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100/loki/api/v1/push")

logging_loki.emitter.LokiEmitter.level_tag = "level"
loki_handler = logging_loki.LokiHandler(
    url=LOKI_URL,
    tags={"application": "gateway"},
    version="1",
)
loki_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

gateway_logger = logging.getLogger("gateway")
gateway_logger.setLevel(logging.INFO)
gateway_logger.addHandler(loki_handler)

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

APP1_URL = os.getenv("APP1_URL", "http://flask-app-1-service:5000")
APP2_URL = os.getenv("APP2_URL", "http://flask-app-2-service:5000")

# Initialize Kubernetes client
config.load_incluster_config()

k8s_apps_api = client.AppsV1Api()
NAMESPACE = os.getenv("NAMESPACE", "default")
APP1_DEPLOYMENT = os.getenv("APP1_DEPLOYMENT", "flask-app-1")
APP2_DEPLOYMENT = os.getenv("APP2_DEPLOYMENT", "flask-app-2")


@app.route('/')
def health():
    app.logger.info('Health check requested')
    return jsonify({"status": "Gateway is running!"})

@app.route('/run-fire-detector', methods=['POST'])
def gateway():
    app.logger.info('Forwarding request to app1')
    start_time_app1 = time.time()
    app1_response = requests.post(
        f"{APP1_URL}/run-fire-detector-1",
        headers={'X-Request-ID': str(g.request_id)}
    )
    elapsed_time_app1 = time.time() - start_time_app1
    gateway_logger.info(f"ID: {g.request_id} | {APP1_DEPLOYMENT} response time: {elapsed_time_app1} seconds")
    app.logger.info('Received response from app1')
    app1_data = app1_response.json()    

    app.logger.info('Forwarding request to app2')
    start_time_app2 = time.time()
    app2_response = requests.post(
        f"{APP2_URL}/run-fire-detector-2",
        json=app1_data,
        headers={'X-Request-ID': str(g.request_id)}
    )
    elapsed_time_app2 = time.time() - start_time_app2
    gateway_logger.info(f"ID: {g.request_id} | {APP2_DEPLOYMENT} response time: {elapsed_time_app2} seconds")
    app.logger.info('Received response from app2')

    app2_json = app2_response.json()
    app2_json['app1_response_time_sec'] = elapsed_time_app1
    app2_json['app2_response_time_sec'] = elapsed_time_app2

    return jsonify(app2_json)

@app.route('/scale', methods=['POST'])
def scale_app():
    """
    Scale the number of instances for flask-app-1 or flask-app-2
    
    Expected JSON payload:
    {
        "app": "flask-app-1" or "flask-app-2",
        "instances": <number of instances>
    }
    """
    data = request.get_json()
    
    if not data or "app" not in data or "instances" not in data:
        return jsonify({"error": "Missing required parameters 'app' and 'instances'"}), 400
    
    app_name = data["app"]
    instances = data["instances"]
    
    if app_name not in ["flask-app-1", "flask-app-2"]:
        return jsonify({"error": "App must be either 'flask-app-1', 'flask-app-2'"}), 400
    
    try:
        instances = int(instances)
        if instances < 1:
            return jsonify({"error": "Number of instances must be at least 1"}), 400
    except ValueError:
        return jsonify({"error": "Instances must be a valid integer"}), 400

    try:
        # Get the deployment
        deployment = k8s_apps_api.read_namespaced_deployment(name=app_name, namespace=NAMESPACE)

        # Update replicas
        deployment.spec.replicas = instances

        # Apply the update
        k8s_apps_api.patch_namespaced_deployment(
            name=app_name,
            namespace=NAMESPACE,
            body=deployment
        )

        app.logger.info(f"Scaled {app_name} to {instances} instances")
        return jsonify({
            "success": True,
            "app": app_name,
            "instances": instances
        })
        
    except client.rest.ApiException as e:
        app.logger.error(f"Kubernetes API error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"Failed to scale {app_name}"
        }), 500
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred"
        }), 500

@app.route('/scale-status', methods=['GET'])
def scale_status():
    """Get the current number of instances for each app"""
    try:
        
        app1_deployment = k8s_apps_api.read_namespaced_deployment(name=APP1_DEPLOYMENT, namespace=NAMESPACE)
        app2_deployment = k8s_apps_api.read_namespaced_deployment(name=APP2_DEPLOYMENT, namespace=NAMESPACE)
        
        app1_replicas = app1_deployment.spec.replicas
        app2_replicas = app2_deployment.spec.replicas
        
        return jsonify({
            "flask-app-1": {
                "deployment": APP1_DEPLOYMENT,
                "instances": app1_replicas,
                "available": app1_deployment.status.available_replicas or 0
            },
            "flask-app-2": {
                "deployment": APP2_DEPLOYMENT,
                "instances": app2_replicas,
                "available": app2_deployment.status.available_replicas or 0
            }
        })
        
    except client.rest.ApiException as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to get deployment status",
        }), 500
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An unexpected error occurred"
        }), 500

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)
