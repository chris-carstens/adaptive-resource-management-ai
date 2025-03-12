# Flask Application with Kubernetes

This guide explains how to build, deploy, and manage a Flask application in a Kubernetes cluster using Minikube.

## Prerequisites
- Minikube installed
- Docker installed
- kubectl installed
- Python and Flask installed

## Initial Setup and Deployment

### 1. Configure Docker Environment
```bash
# Configure shell to use Minikube's Docker daemon
eval $(minikube docker-env)
```

### 2. Set Up Local Registry
```bash
# Start a local Docker registry
docker run -d -p 5000:5000 --name registry registry:2
```

### 3. Build and Push Docker Image
```bash
# Build the Flask application image
docker build -t flask-app:latest .

# Tag the image for local registry
docker tag flask-app:latest localhost:5000/flask-app:latest

# Push the image to local registry
docker push localhost:5000/flask-app:latest
```

### 4. Deploy to Kubernetes
```bash
# First-time deployment
kubectl apply -f flask-app.yaml

# For subsequent updates (only if deployment exists)
kubectl rollout restart deployment flask-app
```

### 5. Verify Deployment
```bash
# Check deployment status
kubectl get deployments

# Check if pods are running
kubectl get pods

# Check service status
kubectl get services
```

### 6. Access the Application
```bash
# Create a URL and open the service in browser
minikube service flask-app-service
```

## Monitoring and Troubleshooting

### View Application Logs
```bash
# View logs in real-time
kubectl logs --timestamps=true <pod-name>
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

## Troubleshooting
- If pods show `ImagePullBackOff`, check if the image was properly pushed to the local registry
- If pods show `CrashLoopBackOff`, check the pod logs for application errors
- If service is not accessible, verify the service configuration and pod labels match

## Additional Resources
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)