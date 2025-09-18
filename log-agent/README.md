# Agent Setup and Monitoring Guide

## Prerequisites
- Python 3.8+
- Required Python packages:
```bash
pip install -r requirements.txt
```

## Agent Configuration

### 1. Environment Variables
Check all the env variables default values defined in the config.py file and change them through a .env file if needed.

### 2. Run the Agents

#### Basic usage:
```bash
# Specify a custom time window in seconds, which is is the window for collecting metrics from now to the past
python3 main.py --app flask-app-1 --time-window 60.0 --rl-agent-port 5001
python3 main.py --app flask-app-2 --time-window 60.0 --rl-agent-port 5002
```
