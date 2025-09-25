# Adaptive Resource Management AI

This project implements an adaptive resource management system for containerized applications using Kubernetes, Flask, and AI-based scaling with reinforcement learning.

## Project Structure

The project is organized into the following main components:

1. **Flask Application** - A distributed application with microservices that run a pipeline of a ML model.
2. **Log Agent** - A monitoring agent that collects metrics and logs from the application.
3. **Requests Generator** - A tool for requests injection
4. **Random Agent** - A random agent that makes scaling decisions randomly for testing purposes. Same API as Agent API
5. **Agent** - RL API checkpoint for scaling decisions based on metrics

## Getting Started

### Prerequisites
- Minikube
- Docker
- kubectl
- Python 3.11
- Helm (for Prometheus installation)

### Quick Start

1. Start the Flask Application. Go to [Flask Application](flask-app/README.md) for more details.
2. Start the RL Agent. Go to [Agent](agent/README.md) for more details.
3. Start the Log Agent for component 1. Go to [Log Agent](log-agent/README.md) for more details.
4. Start the Log Agent for component 2. Go to [Log Agent](log-agent/README.md) for more details.
5. Run the requests generator. Go to [Requests Generator](requests-generator/README.md) for more details.
6. Run jupyter notebook to plot the results from the log agents. Go to [Notebooks](log-agent/metrics_analysis.ipynb) for more details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
