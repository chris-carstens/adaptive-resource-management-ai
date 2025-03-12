from kubernetes import client, config
from flask import Flask, jsonify, request

app = Flask(__name__)

# Load Kubernetes configuration
config.load_incluster_config() # Just for running inside the cluster
api_client = client.ApiClient()
apps_v1 = client.AppsV1Api()

@app.route('/')
def hello_world():
    return 'Hello, World!'

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
