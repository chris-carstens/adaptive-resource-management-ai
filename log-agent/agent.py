import time
from datetime import datetime
import re
from collections import defaultdict
from loki_client import LokiClient
from prometheus_client import PrometheusClient
from rl_agent_client import RLAgentClient
from scale_kubernetes_client import ScaleKubernetesClient
from config import CONFIG

class LogAgent:
    def __init__(self, time_window_minutes: float):
        self.time_window = time_window_minutes
        self.loki_client = LokiClient()
        self.prometheus_client = PrometheusClient()
        self.scale_kubernetes_client = ScaleKubernetesClient()

    def _extract_request_id(self, log_message):
        match = re.search(r'ID: (\d+)', log_message)
        if match:
            return int(match.group(1))
        return None

    def _calculate_mean_request_time(self, request_times):
        completed_requests = []
        for _req_id, times in request_times.items():
            if 'start' in times and 'end' in times:
                duration = times['end'] - times['start']
                completed_requests.append(duration)
        
        if completed_requests:
            return sum(completed_requests) / len(completed_requests)
        return 0

    def _calculate_request_rate(self, request_count: int) -> float:
        # Convert window to seconds for per-second rate
        seconds = self.time_window * 60
        return request_count / seconds if seconds > 0 else 0

    def _unix_to_datetime(self, unix_timestamp):
        return datetime.fromtimestamp(unix_timestamp).isoformat()
    
    def _collect_metrics_by_app(self, application):
        request_times = defaultdict(dict)
        logs = self.loki_client.query_logs(f'{{logger="werkzeug", application="{application}"}}', minutes=self.time_window)

        # Sort all log entries by timestamp
        sorted_logs = []
        for log in logs:
            for value in log.get('values', []):
                sorted_logs.append((float(value[0]), value[1], log.get('stream', {})))
        sorted_logs.sort(key=lambda x: x[0])
        
        # Process logs in chronological order
        for timestamp, message, _stream in sorted_logs:
            timestamp = timestamp / 1e9  # Convert to seconds
            request_id = self._extract_request_id(message)
            
            if request_id:
                if "request arrived" in message:
                    request_times[request_id]['start'] = timestamp
                elif "request completed" in message:
                    if 'start' in request_times[request_id]:
                        request_times[request_id]['end'] = timestamp
                    else:
                        print(f"Warning: Found end time for request {request_id} before start time")

        # Convert timestamps to datetime format for output
        formatted_times = {}
        for req_id, times in request_times.items():
            formatted_times[req_id] = {
                'start': self._unix_to_datetime(times['start']) if 'start' in times else None,
                'end': self._unix_to_datetime(times['end']) if 'end' in times else None
            }

        completed_requests = len([r for r in request_times.values() if 'end' in r])
        requests_per_second = self._calculate_request_rate(completed_requests)

        # Get all pod CPU usages for display
        all_pod_cpu = self.prometheus_client.get_pod_cpu_usage()
        pod_cpu_formatted = {pod: f"{usage:.2f}%" for pod, usage in all_pod_cpu.items()}

        metrics = {
            'application': application,
            'timestamp': datetime.now().isoformat(),
            'time_window_minutes': self.time_window,
            'mean_request_time': self._calculate_mean_request_time(request_times),
            'active_requests': len([r for r in request_times.values() if 'end' not in r]),
            'completed_requests': completed_requests,
            'requests_per_second': requests_per_second,
            "all_pod_cpu_usage": pod_cpu_formatted,
            'request_times': formatted_times
        }

        return metrics  

    def _format_metrics(self, metrics):
        separator = "=" * 80
        app_header = f"\n{separator}\n{' ' * 30}{metrics['application']}\n{separator}"
        
        # Format the basic metrics
        basic_metrics = f"""
Timestamp: {metrics['timestamp']}
Time Window: {metrics['time_window_minutes']} minutes

Performance Metrics:
------------------
Mean Request Time: {metrics['mean_request_time']}
Active Requests: {metrics['active_requests']}
Completed Requests: {metrics['completed_requests']}
Requests per Second: {metrics['requests_per_second']}
"""
        # Add Prometheus CPU usage section with raw query results
        prometheus_metrics = "\nPrometheus CPU Usage (Query Results):\n----------------------------------"
        for pod, usage in metrics['all_pod_cpu_usage'].items():
            prometheus_metrics += f"\n{pod}: {usage}"
        
        # Format the detailed request times
        request_details = "\nDetailed Request Times:\n-------------------"
        for req_id, times in metrics['request_times'].items():
            if times['start'] and times['end']:
                request_details += f"\nRequest {req_id}:"
                request_details += f"\n  Start: {times['start']}"
                request_details += f"\n  End: {times['end']}"
        
        return f"{app_header}{basic_metrics}{prometheus_metrics}{request_details}\n"

    def _collect_metrics(self):
        metrics_app1 = self._collect_metrics_by_app("flask-app-1")
        metrics_app2 = self._collect_metrics_by_app("flask-app-2")
        
        print(self._format_metrics(metrics_app1))
        print(self._format_metrics(metrics_app2))
        print("=" * 80 + "\n")

        metrics = {
            "flask-app-1": metrics_app1,
            "flask-app-2": metrics_app2
        }
        return metrics

    def run(self):
        while True:
            metrics = self._collect_metrics()

            # Get the current status to determine current replicas
            status = self.scale_kubernetes_client.get_scale_status()
            print(f"Current scaling status: {status}")
            app1_replicas = status.get('app1').get('instances')
            app2_replicas = status.get('app2').get('instances')
            
            print(f"Current replicas - App1: {app1_replicas}, App2: {app2_replicas}")
            
            # Get scaling decisions from RL agent
            app1_decision = RLAgentClient(metrics["flask-app-1"], n_replicas=app1_replicas).train()
            app2_decision = RLAgentClient(metrics["flask-app-2"], n_replicas=app2_replicas).train()
            
            n_instances_app_1 = app1_decision.get("n_instances")
            n_instances_app_2 = app2_decision.get("n_instances")
            
            # Only scale if there's a change needed
            if n_instances_app_1 != app1_replicas:
                print(f"Scaling app1 from {app1_replicas} to {n_instances_app_1} instances")
                self.scale_kubernetes_client.scale_app("app1", n_instances_app_1)
            
            if n_instances_app_2 != app2_replicas:
                print(f"Scaling app2 from {app2_replicas} to {n_instances_app_2} instances")
                self.scale_kubernetes_client.scale_app("app2", n_instances_app_2)

            time.sleep(CONFIG['query_interval'])



if __name__ == "__main__":
    LogAgent(time_window_minutes=10.0).run()
