# RL Agent API

A simple API that simulates a Reinforcement Learning agent for resource management.

## Overview

This API receives training data and returns a random decision between 1 and 3.

## Quick Start

### Running Locally

```bash
# Install requirements
pip install -r requirements.txt

# Run the Flask application
python app.py
```


## API Reference

### POST /train

Endpoint to train the RL agent and get a decision.

**Request Body:**

```json
{
  "workload": 0.75,
  "utilization": 0.85,
  "pressure": 0.65,
  "queue_length_dominant": 0.45
}
```

**Response:**

```json
{
  "n_instances": 2,
}
```

## Testing the API

```bash
curl -X POST http://localhost:5001/train \
  -H "Content-Type: application/json" \
  -d '{"workload": 0.75, "utilization": 0.85, "pressure": 0.65, "queue_length_dominant": 0.45}'
```
