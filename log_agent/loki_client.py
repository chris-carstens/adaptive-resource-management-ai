import requests
import time
from config import CONFIG

class LokiClient:
    def __init__(self):
        self.base_url = CONFIG['loki']['url']

    def query_logs(self, query: str) -> list:
        try:
            end = int(time.time() * 1e9)
            start = int((time.time() - 300) * 1e9)  # 5 minutes ago

            response = requests.get(
                f"{self.base_url}/loki/api/v1/query_range",
                params={"query": query, "start": start, "end": end}
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            result = response.json().get('data', {}).get('result', [])
            if not result:
                print(f"No logs found for query: {query}")
            return result
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []