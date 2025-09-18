# RL Agent Setup Guide

This guide provides step-by-step instructions for setting up the Reinforcement Learning (RL) agent using DQN (Deep Q-Network) for adaptive resource management.

## Prerequisites

- Docker
- Python 3.11
- Ray 2.12.0
- Docker Compose

## Setup Instructions

### 1. Build Docker Images

#### Build Base Image
```bash
docker build -f ./src/production_agents/DQN/Dockerfile.base -t rl4cc-base:latest .
```

#### Build Agent Server Image
```bash
bash build_prod_agent_DQN.sh
```

### 2. Python Environment Setup

#### Create Virtual Environment
```bash
python3.11 -m venv .venv
```

#### Activate Virtual Environment
```bash
source .venv/bin/activate
```

#### Install Dependencies
```bash
# Install Ray 2.12.0
pip install ray==2.12.0

# Install Ray client support
pip install "ray[client]"
```

### 3. Start Ray Cluster

Launch the Ray cluster with dashboard and client server:
```bash
ray start --head --dashboard-host 0.0.0.0 --port=6379 --ray-client-server-port=10001
```

**Note**: At this point, you should have:
- Required Docker images built
- Python virtual environment with Ray installed and running
- Ray cluster operational

### 4. Configure Agent Deployment

#### Build and Start the System
```bash
docker compose -f src/production_agents/DQN/docker-compose.yaml up --build
```

Once the system is running, you can interact with the agent at:
```
http://127.0.0.1:5000
```

#### Test the Agent
Use the provided notebook for testing agent interactions:
```
src/production_agents/DQN/agent_deployment_test.ipynb
```
