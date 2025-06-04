import requests
from datetime import datetime, timedelta
from config import CONFIG

class LokiClient:
    def __init__(self):
        self.base_url = CONFIG['loki']['url']

    def query_logs(self, query: str, seconds: float) -> list:
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=seconds)

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