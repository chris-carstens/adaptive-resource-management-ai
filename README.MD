# Flask Application with Kubernetes

This guide explains how to build, deploy, and manage a Flask application in a Kubernetes cluster using Minikube.

## Prerequisites
- Minikube installed
- Docker installed
- kubectl installed
- Python and Flask installed

## Initial Setup and Deployment

### 0. Run Setup and Start Scripts
```bash
# Make scripts executable
chmod +x flask-app/setup.sh
chmod +x flask-app/restart.sh

# Run initial setup script
./setup.sh

# For subsequent restarts/updates
./restart.sh
```

### 1. Start Minikube
```bash
# Start Minikube
minikube start
```

### 2. Configure Docker Environment
```bash
# Configure shell to use Minikube's Docker daemon
eval $(minikube docker-env)
```

### 3. Set Up Local Registry
```bash
docker stop registry

docker rm registry

# Start a local Docker registry
docker run -d -p 5000:5000 --name registry registry:2
```

### 4. Build and Push Docker Images
```bash
# Build the Flask application images
docker build -t flask-app1:latest -f Dockerfile-app1 .
docker build -t flask-app2:latest -f Dockerfile-app2 .

# Tag the images for local registry
docker tag flask-app1:latest localhost:5000/flask-app1:latest
docker tag flask-app2:latest localhost:5000/flask-app2:latest

# Push the images to local registry
docker push localhost:5000/flask-app1:latest
docker push localhost:5000/flask-app2:latest
```

### 5. Set Up Shared Volume
```bash
# Create the shared volume and claim
kubectl apply -f shared-volume.yaml
```

### 6. Apply RBAC Configuration
```bash
# Apply RBAC configuration
kubectl apply -f rbac.yaml
```

### 7. Deploy to Kubernetes
```bash
# First-time deployment
kubectl apply -f flask-app.yaml

# For subsequent updates (only if deployment exists)
kubectl rollout restart deployment flask-app-1
kubectl rollout restart deployment flask-app-2
```

### 8. Verify Deployment
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

### 9. Access the Application
```bash
minikube service flask-app-1-service --url
minikube service flask-app-2-service --url
```

## Monitoring Setup

### 1. Set Up Prometheus
```bash
# Add Prometheus Community Repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus -f prometheus-values.yaml
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

### 3. Set Up Grafana (Optional)
```bash
# Add Grafana repository
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Remove existing Grafana installation if exists
helm uninstall grafana

# Create dashboard ConfigMap
kubectl apply -f grafana-dashboard.yaml

# Install Grafana with dashboard provisioning
helm install grafana grafana/grafana -f grafana-values.yaml

# Wait for Grafana to be ready
kubectl rollout status deployment grafana

# Access Grafana UI
minikube service grafana --url

# Login credentials:
# Username: admin
# Password: admin123
```

### 4. Configure Grafana Data Sources
1. Add Prometheus data source:
   - Name: Prometheus
   - URL: http://prometheus-server:9090  # Internal Kubernetes DNS name
   - Access: Server (Default)
   - Scrape interval: 15s

Note: Do NOT use the Minikube service URL for data sources. The service URL 
(from `minikube service prometheus-server --url`) is only for external browser access
to the Prometheus UI. Inside the cluster, services should use internal Kubernetes DNS names.

2. Add Loki data source:
   - Name: Loki
   - URL: http://loki:3100  # Internal Kubernetes DNS name
   - Access: Server (Default)

## Monitoring and Troubleshooting

### View Application Metrics
```bash
# Access Prometheus UI
minikube service prometheus-server --url

# Access Grafana (if installed)
minikube service grafana --url
```

### View Application Logs
```bash
# View logs in real-time
kubectl logs --timestamps=true <pod-name>

# Query Loki logs through Grafana
# Example LogQL queries:
# - {application="flask-app-1"}
# - {application="flask-app-2"}
```

### Metrics Available
- Matrix multiplication requests: `matrix_multiply_requests_total`
- Matrix multiplication duration: `matrix_multiply_duration_seconds`
- Matrix operations: `matrix_multiply_ops_total`

### Log Tags Available
- matrix_size: Size of matrices being multiplied
- ops_count: Number of multiplication operations
- duration_seconds: Time taken for multiplication
- error_type: Type of error (if any occurred)

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

## API Endpoints

### Scale Deployment
```bash
# Scale to desired number of replicas
curl -X POST -H "Content-Type: application/json" \
     -d '{"replicas": 3}' \
     /scale
```

### Get Deployment Status
```bash
# Get current deployment information
curl /deployment
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
kubectl delete -f prometheus-deployment.yaml
kubectl delete -f loki-deployment.yaml

# Reapply configurations in order
kubectl apply -f shared-volume.yaml
kubectl apply -f rbac.yaml
kubectl apply -f prometheus-config.yaml
kubectl apply -f prometheus-deployment.yaml
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

## Additional Resources
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Agent Setup and Monitoring](README_AGENT.MD)