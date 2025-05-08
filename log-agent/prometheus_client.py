import requests
import time
from config import CONFIG

class PrometheusClient:
    def __init__(self):
        self.base_url = CONFIG['prometheus']['url']

    def query(self, query_str):
        """Execute a Prometheus query and return the results"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/query",
                params={
                    "query": query_str,
                    "time": time.time()
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return None

    def get_pod_cpu_usage(self, application, time_window):
        # TODO: CHECK THE TIME
        """Get CPU usage for all Flask pods directly from the query without calculations"""
        query = f'rate(container_cpu_usage_seconds_total{{pod=~"{application}.*"}}[{int(time_window)}m]) * 100'
        result = self.query(query)

        if not result or result.get('status') != 'success':
            return {}
        
        metrics = result.get('data', {}).get('result', [])
        if metrics:
            # Get last pod with this name. Should be just one pod in the response
            return float(metrics[-1].get('value', [0, 0])[1]) / 100
        return None
