# Flask Applications with Kubernetes

## Prerequisites
- Minikube installed
- Docker installed
- kubectl installed
- Helm installed

## Flask Applications Setup

### 1. Run Setup and Start Scripts
```bash
# Make scripts executable
chmod +x install.sh
chmod +x setup.sh
chmod +x restart.sh

# Install Prerequisites
./install.sh

# Start Minikube
minikube start --cpus=12 --memory=14g # Change the resources if needed by your machine

# Run setup script to build Docker images and deploy the application
./setup.sh

# If you need to rebuild and restart after changes
./restart.sh
```


### 2. Verify Deployment [Optional]
```bash
# Check if pods are running
kubectl get pods -o wide

# View logs in real-time
kubectl logs --timestamps=true <pod-name>
```

### 3. Port Forwarding for Local Development
```bash
# API Gateway
kubectl port-forward service/api-gateway-service 5000:5000
# Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090
# Loki
kubectl port-forward service/loki 3100:3100
```

### 4. Access the Application
The API Gateway provides the following endpoints:

- `GET /` - Health check endpoint
- `POST /run-fire-detector` - Run the fire detection model

```bash
curl -X POST http://localhost:5000/run-fire-detector
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

## Cleanup
```bash
kubectl delete -f flask-app.yaml
kubectl delete pods --all
minikube delete
```

## Additional Resources
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)

kubectl top pods -A
kubectl top node

- free -h
- was running with gunicorn before, now with python directly to see if that changes memory consumption. It was detecting 12 cores and running out of memory
- watch kubectl top pods -A
- watch kubectl top node
we were having crazy request times and inizializations too longs
how to normalize workload? by component? also adding the workloads of each pod?

UPDATE PLOT OF SUM OF TIMES

what workload to normalize
how many workers un unicorn