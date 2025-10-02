import requests
import time
import numpy as np

URL = "http://localhost:5000/run-fire-detector"
DURATION_SECONDS = 5 * 60  # 5 minutes
INTERVAL_SECONDS = 10
NUM_REQUESTS = DURATION_SECONDS // INTERVAL_SECONDS

app1_times = []
app2_times = []

print(f"Sending {NUM_REQUESTS} requests to {URL} every {INTERVAL_SECONDS}s for {DURATION_SECONDS//60} minutes...")

for i in range(int(NUM_REQUESTS)):
    try:
        resp = requests.post(URL)
        print(resp)
        data = resp.json()
        app1_time = data.get("app1_response_time_sec")
        app2_time = data.get("app2_response_time_sec")
        app1_times.append(app1_time)
        app2_times.append(app2_time)
        print(f"Request {i+1}: app1={app1_time:.3f}s, app2={app2_time:.3f}s (status {resp.status_code})")
    except Exception as e:
        print(f"Request {i+1}: failed ({e})")
        app1_times.append(np.nan)
        app2_times.append(np.nan)
    time.sleep(INTERVAL_SECONDS)

# Remove failed requests (NaN)
clean_app1 = [t for t in app1_times if t is not None and not np.isnan(t)]
clean_app2 = [t for t in app2_times if t is not None and not np.isnan(t)]

# Remove 3 max and 3 min outliers for each
def remove_outliers(times):
    if len(times) > 6:
        sorted_times = sorted(times)
        return sorted_times[3:-3]
    return times

filtered_app1 = remove_outliers(clean_app1)
filtered_app2 = remove_outliers(clean_app2)

print(f"\nTotal requests: {len(app1_times)}")
print(f"Valid app1: {len(clean_app1)}, Valid app2: {len(clean_app2)}")
print(f"Filtered app1: {len(filtered_app1)}, Filtered app2: {len(filtered_app2)}")
print(f"Mean app1 response time (filtered): {np.mean(filtered_app1):.3f}s")
print(f"Mean app2 response time (filtered): {np.mean(filtered_app2):.3f}s")
print(f"All filtered app1 times: {filtered_app1}")
print(f"All filtered app2 times: {filtered_app2}")
