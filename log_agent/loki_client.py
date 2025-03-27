import requests
from datetime import datetime, timedelta
from config import CONFIG

class LokiClient:
    def __init__(self):
        self.base_url = CONFIG['loki']['url']

    def query_logs(self, query: str, minutes: float = 5.0) -> list:
        try:
            # Get current time and time window in UTC
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes)
            
            # Convert to nanoseconds since Unix epoch
            end = int(end_time.timestamp() * 1e9)
            start = int(start_time.timestamp() * 1e9)

            print(f"Querying logs from {start_time} to {end_time}")
            
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
            if not result:
                print(f"No logs found for query: {query}")
            return result
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []

    def get_last_cpu_usage(self, minutes: float = 1.0) -> float:
        """Get the last CPU usage percentage from logs"""
        try:
            logs = self.query_logs('{logger="werkzeug"} |~ "CPU Usage:"', minutes=minutes)
            if not logs:
                return None
                
            # Get the last CPU usage log
            for log in logs:
                for value in log.get('values', []):
                    message = value[1]
                    if "CPU Usage:" in message:
                        # Extract CPU percentage from log message
                        try:
                            cpu_str = message.split("CPU Usage:")[1].strip().rstrip('%')
                            return float(cpu_str)
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing CPU value: {e}")
            
            return None
        except Exception as e:
            print(f"Error getting CPU usage from logs: {e}")
            return None