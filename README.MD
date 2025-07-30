# Adaptive Resource Management AI

This project implements an adaptive resource management system for containerized applications using Kubernetes, Flask, and AI-based scaling with reinforcement learning.

## Project Structure

The project is organized into the following main components:

1. **Flask Application** - A distributed application with microservices that run a pipeline of ML model. Go to [Flask Application](flask-app/README.md) for more details
2. **Log Agent** - A monitoring agent that collects metrics and logs from the application. Go to [Log Agent](log-agent/README.md) for more details
3. **JMeter** - A tool for load testing and performance measurement
4. **RL Agent** - A random agent that makes scaling decisions randomly for testing purposes. Same API as Figaro API. Go to [RL Agent](rl-agent/README.md) for more details
5. **Figaro** - RL API checkpoint for scaling decisions based on metrics. Go to [Figaro](figaro/README.md) for more details

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
3. Follow the Log Agent setup instructions. You should run as many instances as Flask Application instances you have
4. Follow the RL Agent / FIGARO setup instructions
5. Run JMeter tests to simulate load on the application

### Port Forwarding for Local Development

```bash
# Prometheus metrics
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090

# Loki logs
kubectl port-forward service/loki 3100:3100

# API Gateway
kubectl port-forward service/api-gateway-service 5000:5000
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
