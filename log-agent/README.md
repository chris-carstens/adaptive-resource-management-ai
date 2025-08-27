# Agent Setup and Monitoring Guide

## Prerequisites
- Python 3.8+
- Required Python packages:
```bash
pip install -r requirements.txt
```

## Agent Configuration

### 1. Environment Variables
Set all the env variables defined in the config.py file

### 2. Run the Agent

#### Basic usage:
```bash
# Specify a custom time window in seconds, which is is the window for collecting metrics from now to the past
python3 main.py --app flask-app-1 --time-window 60.0
python3 main.py --app flask-app-2 --time-window 60.0
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
