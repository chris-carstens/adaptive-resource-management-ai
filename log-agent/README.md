# Agent Setup and Monitoring Guide

## Prerequisites
- Running Kubernetes cluster with the main application (follow main README.MD)
- Python 3.8+
- Required Python packages:
```bash
pip install -r requirements.txt
```

## Agent Configuration

### 1. Port Forward APIs
```bash
# Prometheus metrics
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090

# Loki logs
kubectl port-forward service/loki 3100:3100

# API Gateway
kubectl port-forward service/api-gateway-service 5000:5000
```

### 2. Environment Variables
```bash
export PROMETHEUS_URL="http://localhost:9090"
export LOKI_URL="http://localhost:3100"
export SCALE_KUBERNETES_URL="http://localhost:5000"
```

### 3. Run the Agent
```bash
python3 agent.py
```

## Monitoring

### Available Metrics
The agent monitors:
- CPU usage per pod
- Memory usage per pod
- Request count
- Response times

### Basic Commands
```bash
# View metrics
curl localhost:9090/metrics | grep flask_app

# View application logs
kubectl logs -f deployment/flask-app
```

### Log Queries
```bash
# Basic log query
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={app="flask-app"}' \
  --data-urlencode 'limit=10'

# View live logs
curl -N "http://localhost:3100/loki/api/v1/tail?query={app="flask-app"}"
```

## Troubleshooting

### Common Issues
1. Missing metrics:
   - Check if Prometheus is running
   - Verify Prometheus target configuration
   - Check if metrics endpoint is accessible

2. Can't see logs:
   - Verify pod is running
   - Check log configuration in flask-app deployment
   - Check if Loki is running: `kubectl get pods -l app=loki`
   - Verify Loki port-forward is active
