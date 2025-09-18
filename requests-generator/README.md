# Load Test Script

Generate POST requests to test the defined endpoint of the Flask application.
Requests follow an exponential distribution to simulate real-world traffic.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Edit `main.py` parameters:
- `rate`: requests per second per user
- `users`: number of concurrent users
- `T`: total time in seconds

```bash
python3 main.py
```
