import requests
from config import CONFIG

class RLAgentClient:
    def __init__(self, metrics, n_replicas):
        self.base_url = CONFIG['rl_agent']['url']
        self.metrics = metrics
        self.n_replicas = n_replicas
        self.response_time_threshold = CONFIG['rl_agent']['response_time_threshold']

    def train(self):
        body = {
            "workload": self._workload(),
            "utilization": self._utilization(),
            "pressure": self._pressure(),
            "queue_length_dominant": self._queue_length_dominant(),
        }
        try:
            response = requests.post(
                f"{self.base_url}/train",
                body=body
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling RL Agent: {e}")
            return None

    def _workload(self, application):
        pass

    def _utilization(self, application):
        pass

    def _pressure(self, application_1, application_2):
        # TODO: How to calculate the pressure
        return (self._response_time_by_partition(application_1) + self._response_time_by_partition(application_2))) / self.response_time_threshold

    def _queue_length_dominant(self, application_1, application_2):
        dominant_partition = self._dominant_partition(application_1, application_2)
        return (self._response_time_by_partition(dominant_partition) - self._demand_by_partition(dominant_partition)) / self._demand_by_partition(dominant_partition)

    def _dominant_partition(self, application_1, application_2):
        partition_1 = self._utilization_by_partition(application_1)
        partition_2 = self._utilization_by_partition(application_2)
        if partition_1 >= partition_2:
            return application_1
        return application_2
    
    def _utilization_by_partition(self, application):
        self._workload_by_partition(application) * self._demand_by_partition(application) / self.n_replicas

    def _workload_by_partition(self, application):
        return self.metrics[application]["requests_per_second"]
    
    def _demand_by_partition(self, application):
        # TODO: check how to calculate and difference with request time
        pass

    def _response_time_by_partition(self, application):
        return self.metrics[application]["mean_request_time"]
