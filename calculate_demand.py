import requests
import argparse
import json
import time
import statistics

def calculate_demand(n_requests):
    """
    Calls the /run-fire-detector endpoint n_requests times and calculates
    the average processing time for app1 and app2.
    """
    app1_times = []
    app2_times = []
    url = "http://localhost:5000/run-fire-detector"

    print(f"Running {n_requests} requests to {url} to calculate demand...")

    for i in range(n_requests):
        try:
            response = requests.post(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            app1_time = data.get("app1_response_time_sec")
            app2_time = data.get("app2_response_time_sec")

            if app1_time is not None and app2_time is not None:
                app1_times.append(app1_time)
                app2_times.append(app2_time)
                print(f"Request {i+1}/{n_requests}: app1_time={app1_time:.4f}s, app2_time={app2_time:.4f}s")
            else:
                print(f"Request {i+1}/{n_requests}: Invalid response format. Missing processing times.")

        except requests.exceptions.RequestException as e:
            print(f"Request {i+1}/{n_requests} failed: {e}")
        except json.JSONDecodeError:
            print(f"Request {i+1}/{n_requests}: Failed to decode JSON from response.")
        
        time.sleep(5)

    if not app1_times or not app2_times:
        print("\nCould not calculate demand. No valid processing times were received.")
        return

    avg_app1_demand = statistics.mean(app1_times)
    avg_app2_demand = statistics.mean(app2_times)

    print("\n--- Demand Calculation Results ---")
    print(f"Average demand for app1: {avg_app1_demand:.4f} seconds")
    print(f"Average demand for app2: {avg_app2_demand:.4f} seconds")
    print("----------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate demand for app1 and app2.")
    parser.add_argument("n_requests", type=int, help="Number of requests to send to the endpoint.")
    args = parser.parse_args()

    calculate_demand(args.n_requests)
