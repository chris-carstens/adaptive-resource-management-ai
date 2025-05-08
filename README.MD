# Adaptive Resource Management AI

This project implements an adaptive resource management system for containerized applications using Kubernetes, Flask, and AI-based monitoring with reinforcement learning for intelligent scaling.

## Project Structure

The project is organized into three main components:

1. **Flask Application** - A distributed application with microservices that demonstrate ML model training workloads
2. **Log Agent** - A monitoring agent that collects metrics and logs from the application
3. **RL Agent** - A reinforcement learning agent that makes scaling decisions based on collected metrics

### Directory Structure

- `/flask-app/` - Contains the Flask microservices application, Kubernetes manifests, and deployment scripts
  - `app1.py` - First microservice for data preprocessing and initial model training
  - `app2.py` - Second microservice for completing model training
  - `gateway.py` - API Gateway that routes requests between services
  - `flask-app.yaml` - Kubernetes deployment configuration
  - `rbac.yaml` - Role-based access control configuration
  - `loki-deployment.yaml` - Log aggregation service deployment
  - `design_to_k8s/` - Design-time to Kubernetes manifest conversion tools

- `/log-agent/` - Contains monitoring agent components
  - `agent.py` - Main monitoring agent that collects metrics and logs
  - `loki_client.py` - Client for fetching logs from Loki
  - `prometheus_client.py` - Client for querying metrics from Prometheus
  - `scale_kubernetes_client.py` - Client for scaling Kubernetes resources

- `/rl-agent/` - Contains reinforcement learning agent components
  - `app.py` - API server that responds to scaling requests based on metrics

## Getting Started

### Prerequisites
- Minikube
- Docker
- kubectl
- Python 3.8+
- Helm (for Prometheus installation)

### Quick Start

1. Clone this repository
2. Follow the Flask Application setup instructions
3. Set up the monitoring agent

## Components

### Flask Application

The Flask application consists of three microservices:

1. **API Gateway** - Routes requests between services and handles Kubernetes scaling operations
2. **App1** - Handles dataset downloading and preprocessing, builds and trains the first part of ML model for fire detection
3. **App2** - Completes the machine learning model training and evaluates the results

For detailed setup and usage instructions, see the [Flask Application README](flask-app/README.md).

### Log Agent

The Log Agent collects metrics and logs from the application and provides insights into the application's performance and resource usage:

- Collects request timing information
- Monitors CPU and memory usage
- Tracks request rates and completion times
- Communicates with the Reinforcement Learning agent for scaling decisions

For detailed setup and monitoring instructions, see the [Log Agent README](log-agent/README.md).

### RL Agent

The Reinforcement Learning Agent receives metrics from the Log Agent and makes scaling decisions:

- Provides an API for receiving application metrics
- Makes scaling decisions based on workload, utilization, pressure, and queue length

For detailed information on the RL Agent, see the [RL Agent README](rl-agent/README.md).

## Monitoring Setup

The project uses the following monitoring stack:
- Prometheus for metrics collection
- Loki for log aggregation
- Custom agents for metrics processing and decision making

### Port Forwarding for Local Development

```bash
# Prometheus metrics
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090

# Loki logs
kubectl port-forward service/loki 3100:3100

# API Gateway
kubectl port-forward service/api-gateway-service 5000:5000
```

## Fire Detection ML Pipeline

The project implements a distributed machine learning pipeline for fire detection:

1. App1 downloads a forest fire dataset and processes images using CNN layers
2. Extracted features are passed to App2
3. App2 completes the model training and evaluates performance metrics

The pipeline demonstrates how ML workloads can be distributed and how resource usage can be monitored and optimized.

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
