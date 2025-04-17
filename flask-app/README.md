# Flask Application with Kubernetes

This guide explains how to build, deploy, and manage a Flask application in a Kubernetes cluster using Minikube.

## Prerequisites
- Minikube installed
- Docker installed
- kubectl installed
- Python installed

## Initial Setup and Deployment

### 1. Run Setup and Start Scripts
```bash
# Make scripts executable
chmod +x flask-app/setup.sh
chmod +x flask-app/restart.sh

# Run initial setup script
minikube start
eval $(minikube docker-env)
./setup.sh

# For subsequent restarts/updates
eval $(minikube docker-env)
./restart.sh
```

### 2. Verify Deployment
```bash
# Check events in case of error
kubectl get events

# Check deployment status
kubectl get deployments

# Check if pods are running
kubectl get pods

# Check service status
kubectl get services
```

### 3. Access the Application
```bash
minikube service api-gateway-service --url
```

## Application Architecture

The application consists of three components that communicate via HTTP requests:

1. **API Gateway**: Routes and manages requests to the microservices
2. **Flask App 1**: Handles the first part of the machine learning pipeline
3. **Flask App 2**: Handles the second part of the machine learning pipeline

The communication flow is:
- User → API Gateway
- API Gateway → App 1
- App 1 processes request and sends data to App 2
- App 2 completes processing and returns results
- Results returned to user through the API Gateway

## Gateway Endpoints

The API Gateway provides the following endpoints:

- `GET /health` - Health check endpoint
- `GET /api/run-fire-detector` - Run the fire detection model training

## Monitoring Setup

### 1. Set Up Prometheus
```bash
kubectl create namespace monitoring

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.enabled=false \
  --set alertmanager.enabled=false

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

## Monitoring and Troubleshooting

### View Application Metrics
```bash
### View Application Logs
```bash
# View logs in real-time
kubectl logs --timestamps=true <pod-name>

# Query Loki logs through Grafana
# Example LogQL queries:
# - {application="flask-app-1"}
# - {application="flask-app-2"}
```

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

### Making Changes
```bash
# Edit deployment configuration
kubectl edit deployment flask-app

# Apply configuration changes
kubectl apply -f flask-app.yaml

# Watch for changes in pods
kubectl get pods -w
```

## Cleanup
```bash
# Delete deployment
kubectl delete -f flask-app.yaml

# Stop Minikube
minikube stop
```

## Full System Restart
```bash
# Delete all deployments
kubectl delete -f flask-app.yaml
kubectl delete -f loki-deployment.yaml

# Reapply configurations in order
kubectl apply -f rbac.yaml
kubectl apply -f loki-config.yaml
kubectl apply -f loki-deployment.yaml
kubectl apply -f flask-app.yaml

# Verify all components are running
kubectl get pods -w
```

## Troubleshooting
- If pods show `ImagePullBackOff`, check if the image was properly pushed to the local registry
- If pods show `CrashLoopBackOff`, check the pod logs for application errors
- If service is not accessible, verify the service configuration and pod labels match
- If gateway fails to connect to services, check the service names and ports in environment variables

## Additional Resources
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Agent Setup and Monitoring](README_AGENT.MD)
