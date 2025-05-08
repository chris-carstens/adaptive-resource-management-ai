import os

CONFIG = {
    "query_interval": 5,  # seconds
    'loki': {
        'url': os.getenv('LOKI_URL', 'http://localhost:3100'),
    },
    'prometheus': {
        'url': os.getenv('PROMETHEUS_URL', 'http://localhost:9090'),
    },
    'rl_agent': {
        'url': os.getenv('RL_AGENT_URL', 'http://localhost:5100'),
        'response_time_threshold': os.getenv('RESPONSE_TIME_THRESHOLD', 0.5),
    },
    'scale_kubernetes': {
        'url': os.getenv('SCALE_KUBERNETES_URL', 'http://localhost:5000'),
    },
}
