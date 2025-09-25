import os

CONFIG = {
    'loki': {
        'url': os.getenv('LOKI_URL', 'http://localhost:3100'),
    },
    'prometheus': {
        'url': os.getenv('PROMETHEUS_URL', 'http://localhost:9090'),
    },
    'rl_agent': {
        "max_workload": 3,
        'pressure_clip_value': 3.0,
        'queue_length_dominant_clip_value': 10.0,
        'max_n_replicas': 5,
        'response_time_threshold': {
            "flask-app-1": 1.1,
            "flask-app-2": 0.8,
        },
        "demand": {
            "flask-app-1": 0.7536123180389404,
            "flask-app-2": 0.5587082195281982,
        },
    },
    'scale_kubernetes': {
        'url': os.getenv('SCALE_KUBERNETES_URL', 'http://localhost:5000'),
    },
}
