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

    def get_pod_cpu_usage(self):
        """Get CPU usage for all Flask pods directly from the query without calculations"""
        query = 'sum by (pod) (rate(container_cpu_usage_seconds_total{pod=~"flask.*"}[1m])) * 100'
        result = self.query(query)
        
        if not result or result.get('status') != 'success':
            return {}
        
        cpu_usage = {}
        for metric in result.get('data', {}).get('result', []):
            pod_name = metric.get('metric', {}).get('pod', 'unknown')
            value = float(metric.get('value', [0, 0])[1])
            cpu_usage[pod_name] = value
            
        return cpu_usage
