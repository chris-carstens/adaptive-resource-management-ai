# Load Test Script

Generate uniform POST requests.

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

## Output

Results saved to `results/timing_results_<timestamp>.json`
