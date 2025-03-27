import time
from datetime import datetime
import re
from collections import defaultdict
from loki_client import LokiClient
from config import CONFIG

class LogAgent:
    def __init__(self, time_window_minutes: float):
        self.time_window = time_window_minutes
        self.loki_client = LokiClient()

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
        cpu_usage = self.loki_client.get_last_cpu_usage(minutes=self.time_window, application=application)

        metrics = {
            'application': application,
            'timestamp': datetime.now().isoformat(),
            'time_window_minutes': self.time_window,
            'mean_request_time': f"{self._calculate_mean_request_time(request_times):.12f}s",
            'active_requests': len([r for r in request_times.values() if 'end' not in r]),
            'completed_requests': completed_requests,
            'requests_per_second': f"{requests_per_second:.10f}",
            "latest_cpu_usage": f"{cpu_usage}%" if cpu_usage is not None else None,
            'request_times': formatted_times
        }

        return metrics  

    def _collect_metrics(self):
        print(self._collect_metrics_by_app("flask-app-1"))
        print()
        print(self._collect_metrics_by_app("flask-app-2"))

    def run(self):
        while True:
            self._collect_metrics()
            time.sleep(CONFIG['loki']['query_interval'])

if __name__ == "__main__":
    LogAgent(time_window_minutes=10.0).run()
