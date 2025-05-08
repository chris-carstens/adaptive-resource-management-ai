import requests
from config import CONFIG

DEMAND_1 = 1
DEMAND_2 = 1

class RLAgentClient:
    def __init__(self, metrics, n_replicas):
        self.base_url = CONFIG['rl_agent']['url']
        self.metrics = metrics
        self.n_replicas = n_replicas
        self.response_time_threshold = CONFIG['rl_agent']['response_time_threshold']

    def action(self):
        observation = {
            "n_instances": self.n_replicas,
            "workload": self._workload(),
            "utilization": self._utilization(),
            "pressure": self._pressure(),
            "queue_length_dominant": self._queue_length_dominant(),
        }
        try:
            response = requests.post(
                f"{self.base_url}/action",
                json={'observation': observation}
            )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling RL Agent: {e}")
            return None

    def _pressure(self, ):
        # TODO: How to calculate the pressure
        return self._response_time() / self.response_time_threshold

    def _queue_length_dominant(self):
        # TODO: CONFIRM
        return (self._response_time() - self._demand()) / self._demand()

    # def _dominant_partition(self, application_1, application_2):
    #     partition_1_utilization = self._utilization(application_1)
    #     partition_2_utilization = self._utilization(application_2)
    #     if partition_1_utilization >= partition_2_utilization:
    #         return application_1
    #     return application_2
    
    def _utilization(self):
        # TODO: metrics dict returns this key giving a pod name, with a number between 0 and 1
        return self.metrics["cpu_usage"]
        # self._workload() * self._demand() / self.n_replicas

    def _workload(self):
        return self.metrics["requests_per_second"]

    def _demand(self):
        # TODO
        return 1
        # if application == "app1":
        #     return DEMAND_1
        # elif application == "app2":
        #     return DEMAND_2
        # raise ValueError(f"Unknown application: {application}")

    def _response_time(self):
        return self.metrics["mean_request_time"]
