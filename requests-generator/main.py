from locust import HttpUser, task
import time
import json
import os
import subprocess
import sys
import random

# --- Parameters ---
mean_rate = 0.5     # Total mean requests per second across all users
T = 60 * 5            # Total time in seconds
users = 30         # Number of concurrent users
endpoint = "/run-fire-detector"
host = "http://localhost:5000"
# ------------------

class RealUserBehavior(HttpUser):
    def wait_time(self):
        """
        Exponential distribution for inter-arrival times
        Rate per user = total_rate / number_of_users
        """
        rate_per_user = mean_rate / users
        inter_arrival_time = random.expovariate(rate_per_user)
        return inter_arrival_time

    def on_start(self):
        """Called when a user starts"""
        self.request_data = []

    @task
    def user_session(self):
        """Make request with pure exponential inter-arrival times"""
        # Make the request
        t0 = time.time()
        with self.client.post(endpoint, catch_response=True) as resp:
            t1 = time.time()
            self.request_data.append({
                "start_time": t0,
                "end_time": t1,
                "duration": t1 - t0,
                "status_code": resp.status_code
            })
        # No additional sleep - wait_time() handles exponential inter-arrival times

    def on_stop(self):
        """Called when a user stops"""
        os.makedirs("results", exist_ok=True)
        filename = f"results/exponential_timing_results_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump({
                "total_requests": len(self.request_data),
                "mean_rate": mean_rate,
                "users": users,
                "requests": self.request_data
            }, f, indent=2)
        print(f"\nSaved {len(self.request_data)} requests to {filename}")

if __name__ == "__main__":
    print(f"Starting Locust test with exponential distribution...")
    print(f"Target: {host}{endpoint}")
    print(f"Mean rate: {mean_rate} req/s across {users} users")
    print(f"Rate per user: {mean_rate/users:.3f} req/s")
    print(f"Duration: {T}s")
    print(f"Expected total requests: ~{int(mean_rate * T)}")
    
    # Command to run Locust headless
    cmd = [
        "locust",
        "-f", __file__,
        "--host", host,
        "-u", str(users),
        "-r", "1",              # Spawn rate
        "-t", f"{T}s",
        "--headless",
        "--stop-timeout", "1"
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
