import time
from datetime import datetime
from loki_client import LokiClient
from metrics_calculator import MetricsCalculator
from config import CONFIG

class LogAgent:
    def __init__(self):
        self.loki_client = LokiClient()
        self.metrics_calculator = MetricsCalculator()

    def collect_metrics(self):
        try:
            logs = self.loki_client.query_logs('{logger="werkzeug"}')
            logs2 = self.loki_client.query_logs('{logger="flask-app-1"}')
            return {
                # 'timestamp': datetime.now().isoformat(),
                # 'error_rate': self.metrics_calculator.calculate_error_rate(logs),
                # 'log_volume': self.metrics_calculator.calculate_log_volume(logs)
            }
        except Exception as e:
            print(f"Error: {e}")
            return None

    def run(self):
        while True:
            metrics = self.collect_metrics()
            if metrics:
                print(f"Metrics: {metrics}")
            time.sleep(CONFIG['loki']['query_interval'])

if __name__ == "__main__":
    LogAgent().run()
