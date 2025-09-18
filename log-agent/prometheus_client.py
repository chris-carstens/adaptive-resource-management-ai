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

    def get_average_cpu_usage(self, application, time_window):
        """Get average CPU usage across all pods"""
        all_pods = self._get_all_pods_cpu_usage(application, time_window)
        if not all_pods:
            return 0

        total_usage = sum(pod['usage'] for pod in all_pods)
        return total_usage / len(all_pods)


    def _get_all_pods_cpu_usage(self, application, time_window):
        """Get CPU usage for all pods of an application"""
        query = f'rate(container_cpu_usage_seconds_total{{pod=~"{application}.*"}}[{int(time_window)}s])'
        result = self.query(query)
        
        if not result or result.get('status') != 'success':
            return []
        
        metrics = result.get('data', {}).get('result', [])
        pod_usages = []
        
        for metric in metrics:
            pod_name = metric.get('metric', {}).get('pod', 'unknown')
            usage = float(metric.get('value', [0, 0])[1])
            pod_usages.append({'pod': pod_name, 'usage': usage})
        
        return pod_usages