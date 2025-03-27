import requests
from datetime import datetime, timedelta
from config import CONFIG

class LokiClient:
    def __init__(self):
        self.base_url = CONFIG['loki']['url']

    def query_logs(self, query: str, minutes: float) -> list:
        try:
            # Get current time and time window in UTC
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes)
            
            end = int(end_time.timestamp() * 1e9)
            start = int(start_time.timestamp() * 1e9)

            response = requests.get(
                f"{self.base_url}/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": start,
                    "end": end,
                    "limit": 5000,
                    "direction": "forward"
                }
            )
            response.raise_for_status()
            result = response.json().get('data', {}).get('result', [])
            return result
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []

    def get_last_cpu_usage(self, minutes: float, application: str) -> float:
        """Get the last CPU usage percentage from logs"""
        try:
            logs = self.query_logs(f'{{logger="werkzeug", application="{application}"}} |~ "CPU Usage:"', minutes=minutes)
            if not logs:
                return None
                
            # Sort all log entries by timestamp (newest first)
            sorted_values = []
            for log in logs:
                sorted_values.extend([
                    (float(value[0]), value[1])  # timestamp, message
                    for value in log.get('values', [])
                ])
            sorted_values.sort(key=lambda x: x[0], reverse=True)

            # Get the most recent CPU usage
            for _, message in sorted_values:
                    cpu_str = message.split("CPU Usage:")[1].strip().rstrip('%')
                    return float(cpu_str)
            return None
        except Exception as e:
            print(f"Error getting CPU usage from logs: {e}")
            return None