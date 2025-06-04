import requests
from config import CONFIG

class RLAgentClient:
    def __init__(self, metrics, n_replicas, app_name):
        self.base_url = CONFIG['rl_agent']['url']
        self.metrics = metrics
        self.n_replicas = n_replicas
        self.response_time_threshold = CONFIG['rl_agent']['response_time_threshold']
        self.demand = CONFIG['rl_agent']['demand'][app_name]

    def action(self):
        observation = {
            "n_instances": self.n_replicas,
            "workload": self._workload(),
            "utilization": self._utilization(),
            "pressure": self._pressure(),
            "queue_length_dominant": self._queue_length_dominant(),
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

    def _pressure(self):
        return self._response_time() / self.response_time_threshold

    def _queue_length_dominant(self):
        # TODO: CONFIRM. How do we define a component here? Is it just one component in each flask app ane calculated separately?
        return (self._response_time() - self._demand()) / self._demand()
    
    def _utilization(self):
        return self.metrics["cpu_usage"]
        # self._workload() * self._demand() / self.n_replicas

    def _workload(self):
        return self.metrics["requests_per_second"]

    def _demand(self):
        return self.demand

    def _response_time(self):
        # TODO: CHECK TO USE RESPONSE TIME, MEASURING BEGINNING OF REQUEST FROM JMETER
        return self.metrics["mean_request_time"]
