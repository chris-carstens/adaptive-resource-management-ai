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

# Start Minikube with default resources 
# Note: Default resources vary by driver and system but are typically 2 CPUs and 4GB memory
minikube start --nodes=1

# To customize resources and other configurations, use:
# minikube start --nodes=1 --cpus=2 --memory=4096MB --disk-size=20GB --driver=docker

# To check allocated resources after starting:
# kubectl get nodes -o=jsonpath="{.items[0].status.capacity}"

./setup.sh

# If you need to rebuild and restart after changes:
./restart.sh
```

### 2. Port Forwarding for Local Development
```bash
# API Gateway
kubectl port-forward service/api-gateway-service 5000:5000
# Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090
# Loki
kubectl port-forward service/loki 3100:3100
```

### 2. Verify Deployment [Optional]
```bash
# Check nodes
kubectl get nodes

# Check deployment status
kubectl get deployments

# Check if pods are running
kubectl get pods -o wide

# Check service status
kubectl get services

# Check monitoring pods
kubectl get pods -n monitoring

# Verify Loki deployment
kubectl get pods -l app=loki

# View logs in real-time
kubectl logs --timestamps=true <pod-name>

# Get detailed information about a pod
kubectl describe pod <pod-name>

# Get service details
kubectl get svc

# Check deployment status
kubectl rollout status deployment/flask-app

```

### 3. Access the Application
The API Gateway provides the following endpoints:

- `GET /` - Health check endpoint
- `POST /run-fire-detector` - Run the fire detection model

```bash
# Example using curl
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


- Verify the metric calculations.
- Try a loop with real values using this calculations comparing with the group.
- Check the point that they mentioned about avoiding the delay.
- Case that the number of pods is above the limit.
- Also check when the action returns an error or -1.
- Run with a real workload from JMeter.
- What about the checkpoints and warmup excutions.
- what is the difference between service time and response time. How is computed the service time.


- Implement the response time (instead of the service time as currently done).
- Pending: How to calculate the request time for the API Gateway.
- Why service time is changing?
- Adjust constants metrics for pressure, demand, threshold.
- Calculate the demmand.

Meeting:
- Tune the values like demand and threshold for the pressure to try final version of FIGARO.
- Implement the response time with the value that comes from JMETER.
- Why setvice time is changing?