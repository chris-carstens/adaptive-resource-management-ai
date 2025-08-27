# Load Test Script

A load testing script that generates uniform POST requests over a specified time period.

## Usage

```python
python3 main.py
```

## Configuration

Edit the following parameters in `load_test.py`:

- `rate`: Requests per second
- `T`: Total time in seconds  
- `endpoint`: Target URL

## Output

The script generates `timing_results.json` containing timing data for each request.
