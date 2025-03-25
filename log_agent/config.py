import os

CONFIG = {
    'loki': {
        'url': os.getenv('LOKI_URL', 'http://localhost:3100'),
        'query_interval': 5  # seconds
    }
}
