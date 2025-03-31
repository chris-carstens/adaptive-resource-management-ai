# Adaptive Resource Management AI

This project implements an adaptive resource management system for containerized applications using Kubernetes, Flask, and AI-based monitoring.

## Project Structure

The project is organized into two main components:

1. **Flask Application** - A distributed application with two microservices that demonstrate ML model training workloads
2. **Log Agent** - A monitoring agent that collects metrics and logs from the application

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

The Flask application consists of two microservices that work together to process machine learning workloads. The first service handles data preprocessing and initial model training, while the second service completes the model training pipeline.

For detailed setup and usage instructions, see the [Flask Application README](flask-app/README.md).

### Log Agent

The Log Agent collects metrics and logs from the application and provides insights into the application's performance and resource usage.

For detailed setup and monitoring instructions, see the [Log Agent README](log-agent/README.md).

## Monitoring Setup

The project uses the following monitoring stack:
- Prometheus for metrics collection
- Loki for log aggregation

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
