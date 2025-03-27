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