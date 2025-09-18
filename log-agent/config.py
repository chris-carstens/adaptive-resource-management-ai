import os

CONFIG = {
    'loki': {
        'url': os.getenv('LOKI_URL', 'http://localhost:3100'),
    },
    'prometheus': {
        'url': os.getenv('PROMETHEUS_URL', 'http://localhost:9090'),
    },
    'rl_agent': {
        'pressure_clip_value': 3.0,
        'queue_length_dominant_clip_value': 10.0,
        'max_n_replicas': 5,
        'response_time_threshold': {
            "flask-app-1": os.getenv('FLASK_APP1_THRESHOLD', 2.5),
            "flask-app-2": os.getenv('FLASK_APP2_THRESHOLD', 0.5),
        },
        "demand": {
            "flask-app-1": os.getenv('FLASK_APP1_DEMAND', 0.9302),
            "flask-app-2": os.getenv('FLASK_APP2_DEMAND', 0.1760),
        },
    },
    'scale_kubernetes': {
        'url': os.getenv('SCALE_KUBERNETES_URL', 'http://localhost:5000'),
    },
}
