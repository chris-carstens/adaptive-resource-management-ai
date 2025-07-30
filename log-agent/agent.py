import time
from datetime import datetime
import re
import argparse
import json
from collections import defaultdict
from loki_client import LokiClient
from prometheus_client import PrometheusClient
from rl_agent_client import RLAgentClient
from scale_kubernetes_client import ScaleKubernetesClient
from config import CONFIG

class LogAgent:
    def __init__(self, time_window: float, app_name: str):
        self.time_window = time_window
        self.app_name = app_name
        self.loki_client = LokiClient()
        self.prometheus_client = PrometheusClient()
        self.scale_kubernetes_client = ScaleKubernetesClient()
        self.instance_history = []
        self.start_time = time.time()

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
        return request_count / self.time_window

    def _unix_to_datetime(self, unix_timestamp):
        return datetime.fromtimestamp(unix_timestamp).isoformat()
    
    def _extract_gateway_response_time(self, log_message):
        """Extract response time from gateway logs in format: ID | APP_NAME response time: X seconds"""
        if " | " in log_message and " response time: " in log_message and self.app_name in log_message:
            try:
                parts = log_message.split(" | ", 1)
                rest_part = parts[1]
                
                time_str = rest_part.split(" response time: ")[1].split(" seconds")[0]
                response_time = float(time_str)
                
                return response_time
            except (ValueError, IndexError):
                return None
        return None

    def _collect_metrics_by_app(self, application):
        request_times = defaultdict(dict)
        logs = self.loki_client.query_logs(f'{{logger="werkzeug", application="{application}"}}', seconds=self.time_window)

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

        metrics = {
            'application': application,
            'timestamp': datetime.now().isoformat(),
            'time_window': self.time_window,
            'mean_request_time': self._calculate_mean_request_time(request_times),
            'active_requests': len([r for r in request_times.values() if 'end' not in r]),
            'completed_requests': completed_requests,
            'total_arrived_requests': len(request_times),
            'arrival_rate': len(request_times) / self.time_window,
            'requests_per_second': self._calculate_request_rate(completed_requests),
            "cpu_usage": self.prometheus_client.get_pod_cpu_usage(application=application, time_window=self.time_window),
            'request_times': formatted_times
        }

        return metrics  

    def _collect_gateway_response_metrics(self):
        """Collect response time metrics from gateway logs"""
        app_response_times = []
        
        logs = self.loki_client.query_logs('{application="gateway"}', seconds=self.time_window)
        
        for log in logs:
            for value in log.get('values', []):
                message = value[1]
                response_time = self._extract_gateway_response_time(message)
                if response_time is not None:
                    app_response_times.append(response_time)

        return {
                'response_count': len(app_response_times),
                'mean_response_time': sum(app_response_times) / len(app_response_times) if app_response_times else 0,
            }


    def _format_metrics(self, metrics):
        separator = "=" * 80
        app_header = f"\n{separator}\n{' ' * 30}{metrics['application']}\n{separator}"
        
        # Format the basic metrics
        basic_metrics = f"""
Timestamp: {metrics['timestamp']}
Time Window: {metrics['time_window']} seconds

Performance Metrics:
------------------
Mean Request Time: {metrics['mean_request_time']}
Active Requests: {metrics['active_requests']}
Completed Requests: {metrics['completed_requests']}
Total Arrived Requests: {metrics['total_arrived_requests']}
Arrival Rate (req/sec): {metrics['arrival_rate']:.3f}
Requests per Second: {metrics['requests_per_second']}
"""

        # Add Prometheus CPU usage section with raw query results
        prometheus_metrics = f"\nPrometheus CPU Usage (Query Results): {metrics['cpu_usage']}"
        # Format the detailed request times
        request_details = "\nDetailed Request Times:\n-------------------"
        for req_id, times in metrics['request_times'].items():
            if times['start'] and times['end']:
                request_details += f"\nRequest {req_id}:"
                request_details += f"\n  Start: {times['start']}"
                request_details += f"\n  End: {times['end']}"
        
        return f"{app_header}{basic_metrics}{prometheus_metrics}{request_details}\n"
    
    def _format_gateway_response_metrics(self, gateway_metrics):
        """Format gateway response metrics for display"""
        if not gateway_metrics:
            return "\nNo gateway response metrics found.\n"

        header = "\nGATEWAY RESPONSE METRICS:\n" + "=" * 30
        metrics_info = f"\n{gateway_metrics['response_count']} requests, mean: {gateway_metrics['mean_response_time']:.6f}s"

        return f"{header}{metrics_info}\n"
        
    def _collect_metrics(self):
        metrics_app = self._collect_metrics_by_app(self.app_name)
        gateway_response_metrics = self._collect_gateway_response_metrics()
        
        print(self._format_metrics(metrics_app))
        print(self._format_gateway_response_metrics(gateway_response_metrics))
        print("=" * 80 + "\n")
        
        metrics = {
            self.app_name: metrics_app,
            'gateway_responses': gateway_response_metrics
        }
        return metrics

    def run(self):
        instance_history_file = f"{self.app_name}_instance_history.json"
        while True:
            metrics = self._collect_metrics()
            current_time = time.time()
            elapsed_seconds = int(current_time - self.start_time)

            # Get the current status to determine current replicas
            status = self.scale_kubernetes_client.get_scale_status()
            if not status:
                print("Error: Unable to retrieve scaling status.")
                time.sleep(CONFIG['query_interval'])
                continue
            print(f"Current scaling status: {status}")
            app_replicas = status.get(self.app_name).get('instances')
            if metrics[self.app_name]["requests_per_second"] and metrics[self.app_name]["mean_request_time"] and metrics[self.app_name]["cpu_usage"]:
                app_decision = RLAgentClient(metrics[self.app_name], n_replicas=app_replicas, app_name=self.app_name).action()
                n_instances_app = app_decision.get("action")
            else:
                n_instances_app = app_replicas
            
            # Only scale if there's a change needed
            if n_instances_app != app_replicas:
                print(f"Scaling {self.app_name} from {app_replicas} to {n_instances_app} instances")
                self.scale_kubernetes_client.scale_app(self.app_name, n_instances_app)
                print(f"Scaling {self.app_name} from {app_replicas} to {n_instances_app} instances")
            
            # Add gateway response metrics to history if available
            gateway_app_metrics = metrics.get('gateway_responses', {})
            
            # Add current instance data to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "elapsed_seconds": elapsed_seconds,
                "instances": n_instances_app,
                "cpu_usage": metrics[self.app_name]["cpu_usage"],
                "requests_per_second": metrics[self.app_name]["requests_per_second"],
                "mean_request_time": metrics[self.app_name]["mean_request_time"],
                "total_arrived_requests": metrics[self.app_name]["total_arrived_requests"],
                "workload": metrics[self.app_name]["arrival_rate"],
                "gateway_response_count": gateway_app_metrics.get('response_count', 0),
                "gateway_mean_response_time": gateway_app_metrics.get('mean_response_time', 0)
            }
            self.instance_history.append(history_entry)
            # Write updated history to JSON file
            try:
                with open(instance_history_file, 'w') as f:
                    json.dump({
                        "app_name": self.app_name,
                        "history": self.instance_history
                    }, f, indent=2)
                print(f"Instance history updated in {instance_history_file}")
            except Exception as e:
                print(f"Error writing instance history to file: {e}")
            time.sleep(CONFIG['query_interval'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Log Agent for monitoring and scaling applications')
    parser.add_argument('--app', type=str, default="app1",
                        help='Application name to monitor (default: app1)')
    parser.add_argument('--time-window', type=float, default=10.0,
                        help='Time window in seconds for metrics collection (default: 10.0)')
    args = parser.parse_args()
    print(f"Starting Log Agent for application: {args.app}")
    
    LogAgent(time_window=args.time_window, app_name=args.app).run()
