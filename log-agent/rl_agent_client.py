import requests
from config import CONFIG
import numpy as np

class RLAgentClient:
    def __init__(self, metrics, n_replicas, app_name, base_url):
        self.base_url = base_url
        self.metrics = metrics
        self.n_replicas = n_replicas
        self.max_n_replicas = CONFIG['rl_agent']['max_n_replicas']
        self.response_time_threshold = CONFIG['rl_agent']['response_time_threshold'][app_name]
        self.pressure_clip_value = CONFIG['rl_agent']['pressure_clip_value']
        self.queue_length_dominant_clip_value = CONFIG['rl_agent']['queue_length_dominant_clip_value']
        self.demand = CONFIG['rl_agent']['demand'][app_name]
        self.max_workload = CONFIG['rl_agent']['max_workload']

    def action(self):
        observation = {
            "n_instances": self._normalized_n_replicas(),
            "workload": self._normalized_workload(),
            "utilization": self._utilization(),
            "pressure": self._normalized_pressure(),
            "queue_length_dominant": self._normalized_queue_length_dominant(),
        }
        try:
            print('CALLING ACTION WITH: ', observation)
            response = requests.post(
                f"{self.base_url}/action",
                json={'observation': observation}
            )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling RL Agent: {e}")
            return None

    def _normalized_n_replicas(self):
        return self.n_replicas / self.max_n_replicas

    def _normalized_pressure(self):
        """Normalized pressure to [0, 1] range"""
        clipped_pressure = np.clip(self._pressure(), 0, self.pressure_clip_value)
        return clipped_pressure / self.pressure_clip_value

    def _normalized_workload(self):
        clipped_workload = np.clip(self._workload(), 0, self.max_workload)
        return clipped_workload / self.max_workload

    def _pressure(self):
        # TODO: Check MAX
        return self._response_time() / self.response_time_threshold

    def _normalized_queue_length_dominant(self):
        """Normalized queue length to [0, 1] range"""
        clipped_queue_length_dominant = np.clip(self._queue_length_dominant(), 0, self.queue_length_dominant_clip_value)
        return clipped_queue_length_dominant / self.queue_length_dominant_clip_value

    def _queue_length_dominant(self):
        return max(0, (self._response_time() - self._demand()) / self._demand())

    def _utilization(self):
        return self.metrics["cpu_usage"]
        # self._workload() * self._demand() / self.n_replicas

    def _workload(self):
        return self.metrics["requests_per_second"]

    def _demand(self):
        return self.demand

    def _response_time(self):
        return self.metrics["mean_response_time"]
