# Log Agent - Monitoring and Auto-scaling Component

## Overview

The Log Agent is a component of the adaptive resource management system that acts as an intelligent monitoring and scaling orchestrator. It continuously monitors the performance metrics of associated Flask application components and makes intelligent scaling decisions by communicating with the reinforcement learning (RL) agent.

## Core Functions

### 1. **Metrics Collection**
- **Prometheus Integration**: Collects real-time CPU usage
- **Loki Log Aggregation**: Gathers application logs from loki

### 2. **Intelligent Scaling Decisions**
- **RL Agent Communication**: Sends collected metrics to the reinforcement learning agent for scaling decisions
- **Kubernetes Integration**: Executes scaling commands on Kubernetes deployments based on RL agent recommendations

## Agent Workflow

1. **Initialize**: Connect to Prometheus, Loki, and Kubernetes APIs
2. **Monitor**: Continuously collect metrics from the associated component (e.g., flask-app-1 or flask-app-2)
3. **Analyze**: Process metrics over the specified time window
4. **Decide**: Send processed metrics to the RL agent for scaling recommendations
5. **Execute**: Apply scaling decisions to the Kubernetes deployment
6. **Repeat**: Continue the monitoring cycle

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
