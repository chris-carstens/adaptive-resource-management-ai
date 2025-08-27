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

So, the flow to run a test in the project is:
1. Start the Flask Application
2. Start RL/Figaro Agent
3. Start the Log Agent for app 1
4. Start the Log Agent for app 2
5. Run the requests generator
6. Check and move the logs and metrics collected by the Log Agent
7. Run jupyter notebook to plot the results

# TODO:
CALCULATE REAL DEMAND
REVIEW FORMULAS IN LOG AGENT TO INTERACT WITH RL AGENT
SAVE RESULTS AND PLOT ONE VERSION WITH 6 REQUESTS BY MINUTE AND OTHER WITH 3 REQUESTS BY MINUTE
CHECK MEMORY PROBLEMS DELETING IMAGES AND UPDATING THE PORTION OF IMAGES USED
SAVE LOGS AND RESULTS FROM JM IN THE SAME FOLDER INSIDE THE APP


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
