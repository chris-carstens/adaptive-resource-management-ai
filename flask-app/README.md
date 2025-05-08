# Flask Applications with Kubernetes

## Prerequisites
- Minikube installed
- Docker installed
- kubectl installed
- Python installed

## Flask Applications Setup

### 1. Run Setup and Start Scripts
```bash
# Make scripts executable
chmod +x setup.sh
chmod +x restart.sh

minikube start --nodes=1

./setup.sh

# If you need to rebuild and restart after changes:
./restart.sh
```

# Alternatively, you can run the commands manually:
```bash
# Build images directly in Minikube's Docker daemon
minikube image build -t flask-app1:latest -f Dockerfile-app1 . --all
minikube image build -t flask-app2:latest -f Dockerfile-app2 . --all
minikube image build -t flask-app-gateway:latest -f Dockerfile-gateway . --all

# Apply the Kubernetes manifests
kubectl apply -f rbac.yaml
kubectl apply -f flask-app.yaml
```

### 2. Verify Deployment [Optional]
```bash
# Check events in case of error
kubectl get events

# Check nodes
kubectl get nodes

# Check deployment status
kubectl get deployments

# Check if pods are running
kubectl get pods -o wide

# Check service status
kubectl get services
```

### 3. Access the Application
```bash
minikube service api-gateway-service --url
```

## Monitoring Setup

### 1. Set Up Prometheus
```bash
kubectl create namespace monitoring

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.enabled=false \
  --set alertmanager.enabled=false

# Add label (in case is not already added)
kubectl label pods -l app=flask-app-1 monitoring=true
kubectl label pods -l app=flask-app-2 monitoring=true

kubectl get pods -n monitoring
```

### 2. Set Up Loki
```bash
# Apply Loki configurations
kubectl apply -f loki-config.yaml
kubectl apply -f loki-deployment.yaml

# Verify Loki deployment
kubectl get pods -l app=loki

# Stream logs in real-time
kubectl logs -f <loki-pod-name>

# Restart
kubectl delete -f loki-deployment.yaml
kubectl apply -f loki-config.yaml
kubectl apply -f loki-deployment.yaml
```

## Application Architecture

The application consists of three components that communicate via HTTP requests:

1. **API Gateway**: Routes and manages requests to the microservices
2. **Flask App 1**: Handles the first part of the machine learning pipeline
3. **Flask App 2**: Handles the second part of the machine learning pipeline

The communication flow is:
- User → API Gateway
- API Gateway → App 1
- Gateway receives response from App 1
- API Gateway → App 2
- Gateway receives response from App 2
- Results returned to user through the API Gateway

## Gateway Endpoints

The API Gateway provides the following endpoints:

- `GET /` - Health check endpoint
- `GET /api/run-fire-detector` - Run the fire detection model training


### View Application Logs
```bash
# View logs in real-time
kubectl logs --timestamps=true <pod-name>

### Common Commands
```bash
# Get detailed information about a pod
kubectl describe pod <pod-name>

# Get service details
kubectl get svc

# Check deployment status
kubectl rollout status deployment/flask-app

# Scale deployment
kubectl scale deployment flask-app --replicas=3
```

## Cleanup
```bash
kubectl delete -f flask-app.yaml

minikube delete
```

## Additional Resources
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Agent Setup and Monitoring](README_AGENT.MD)

## Design Time to Kubernetes Conversion

You can convert the design time model (JSON) to Kubernetes manifest files using the provided script:

```bash
# Install required libraries
pip install pyyaml

# Make the conversion script executable
chmod +x convert_design_to_k8s.py

# Run the conversion
python3 convert_design_to_k8s.py

# Apply the generated manifest
kubectl apply -f generated-flask-app.yaml
```

This script maps the computational layers defined in `design_time.json` to Kubernetes nodes and components to deployments, following the compatibility matrix constraints.
