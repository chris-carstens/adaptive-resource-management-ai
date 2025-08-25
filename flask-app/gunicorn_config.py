import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes - processor sharing implementation
workers = multiprocessing.cpu_count()  # Async workers
worker_class = "gevent"  # Async for processor sharing
worker_connections = 1000
timeout = 30
keepalive = 5

# Gevent-specific settings for processor sharing
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance
preload_app = False  # Disabled to avoid monkey patch conflicts

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "gunicorn_flask_app_async"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
