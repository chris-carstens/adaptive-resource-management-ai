import os

CONFIG = {
    'loki': {
        'url': os.getenv('LOKI_URL', 'http://localhost:3100'),
    },
    'prometheus': {
        'url': os.getenv('PROMETHEUS_URL', 'http://localhost:9090'),
    },
    'rl_agent': {
        "max_workload": 2,
        'pressure_clip_value': 3.0,
        'queue_length_dominant_clip_value': 10.0,
        'max_n_replicas': 5,
        'response_time_threshold': {
            "flask-app-1": 1.1,
            "flask-app-2": 0.75,
        },
        "demand": {
            "flask-app-1": 0.712,
            "flask-app-2": 0.561,
        },
    },
    'scale_kubernetes': {
        'url': os.getenv('SCALE_KUBERNETES_URL', 'http://localhost:5000'),
    },
}
