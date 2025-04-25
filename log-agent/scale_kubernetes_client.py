import requests
from config import CONFIG

class ScaleKubernetesClient:
    def __init__(self):
        self.base_url = CONFIG.get('scale_kubernetes').get('url')

    def scale_app(self, app_name, n_instances):
        """
        Scale an application to the specified number of instances.
        
        Args:
            app_name (str): The application name ('app1' or 'app2')
            n_instances (int): The number of instances to scale to
        
        Returns:
            dict: The response from the gateway API
        """
        try:
            response = requests.post(
                f"{self.base_url}/scale",
                json={
                    "app": app_name,
                    "instances": n_instances
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error scaling {app_name} to {n_instances} instances: {e}")
            return None

    def get_scale_status(self):
        """
        Get the current scaling status of all applications.
        
        Returns:
            dict: The current scaling status
        """
        try:
            response = requests.get(f"{self.base_url}/scale-status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting scaling status: {e}")
            return None

    def health_check(self):
        """
        Check if the gateway API is healthy.
        
        Returns:
            bool: True if the gateway is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception:
            return False
