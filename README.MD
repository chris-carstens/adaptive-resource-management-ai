# Adaptive Resource Management AI

This project implements an adaptive resource management system for containerized applications using Kubernetes, Flask, and AI-based scaling with reinforcement learning.

## Project Structure

The project is organized into the following main components:

1. **Flask Application** - A distributed application with microservices that run a pipeline of a ML model. Go to [Flask Application](flask-app/README.md) for more details
2. **Log Agent** - A monitoring agent that collects metrics and logs from the application. Go to [Log Agent](log-agent/README.md) for more details
3. **Requests Generator** - A tool for requests injection
4. **Random Agent** - A random agent that makes scaling decisions randomly for testing purposes. Same API as Agent API. Go to [Random Agent](random-agent/README.md) for more details
5. **Agent** - RL API checkpoint for scaling decisions based on metrics. Go to [Agent](agent/README.md) for more details

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
4. Follow the Agent setup instructions
3. Follow the Log Agent setup instructions
5. Run Requests generator to simulate load on the application

So, the flow to run a test in the project is:
1. Start the Flask Application
2. Start the Agent
3. Start the Log Agent for app 1
4. Start the Log Agent for app 2
5. Run the requests generator
6. Check the logs and metrics collected by the Log Agent
7. Run jupyter notebook to plot the results

## License

This project is licensed under the MIT License - see the LICENSE file for details.
