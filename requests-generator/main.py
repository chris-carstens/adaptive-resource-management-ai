from locust import HttpUser, task, constant_pacing
import time
import json
import os
import subprocess
import sys

# --- Parameters ---
rate = 0.14      # Requests per second
T = 180        # Total time in seconds
users = 3       # Number of concurrent users
endpoint = "/run-fire-detector"
host = "http://localhost:5000"
# ------------------

class SimpleUser(HttpUser):
    # Set the wait time to achieve the desired request rate
    wait_time = constant_pacing(1.0 / rate)

    def on_start(self):
        """Called when a user starts"""
        self.request_data = []

    @task
    def post_request(self):
        """Sends a POST request to the specified endpoint"""
        t0 = time.time()
        with self.client.post(endpoint) as resp:
            t1 = time.time()
            self.request_data.append({
                "start_time": t0,
                "end_time": t1,
                "duration": t1 - t0,
                "status_code": resp.status_code
            })

    def on_stop(self):
        """Called when a user stops"""
        os.makedirs("results", exist_ok=True)
        filename = f"results/timing_results_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump({
                "total_requests": len(self.request_data),
                "requests": self.request_data
            }, f, indent=2)
        print(f"\nSaved {len(self.request_data)} requests to {filename}")

if __name__ == "__main__":
    # This block allows running the script directly
    print(f"Starting Locust test...")
    print(f"Target: {host}{endpoint}")
    print(f"Rate: {rate} req/s")
    print(f"Duration: {T}s")
    print(f"Expected requests: {int(rate * T)}")
    
    # Dynamically set the wait_time on the class before running
    SimpleUser.wait_time = constant_pacing(1.0 / rate)

    # Command to run Locust headless
    cmd = [
        "locust",
        "-f", __file__,
        "--host", host,
        "-u", str(users),          # Users
        "-r", "1",          # Spawn rate
        "-t", f"{T}s",      # Run time
        "--headless",
        "--stop-timeout", "1" # Stop quickly after run time
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("\nError: 'locust' command not found.")
        print("Please install Locust: pip install locust")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nLocust test failed with exit code {e.returncode}.")
        sys.exit(1)
