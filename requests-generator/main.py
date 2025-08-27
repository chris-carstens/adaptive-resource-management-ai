import time
import urllib.request
import json
import threading

def send_request(endpoint, request_number, results_list):
    request_start = time.time()
    try:
        req = urllib.request.Request(endpoint, method='POST')
        urllib.request.urlopen(req)
    except:
        pass
    request_end = time.time()
    
    results_list.append({
        "request_number": request_number,
        "start_time": request_start,
        "end_time": request_end,
        "duration": request_end - request_start
    })

def load_test(rate, T, endpoint):
    total_requests = int(T * rate)
    interval = 1.0 / rate if rate > 0 else 0
    
    request_times = []
    threads = []
    
    for i in range(total_requests):
        # Send request in separate thread
        thread = threading.Thread(target=send_request, args=(endpoint, i + 1, request_times))
        thread.start()
        threads.append(thread)
        
        # Sleep for fixed interval regardless of request duration
        if i < total_requests - 1:
            time.sleep(interval)
    
    # Wait for all requests to complete
    for thread in threads:
        thread.join()
    
    # Sort results by request number
    request_times.sort(key=lambda x: x['request_number'])

    results = {
        "total_requests": total_requests,
        "requests": request_times
    }
    
    with open("timing_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Completed {total_requests} requests")
    print(f"Results saved to timing_results.json")

if __name__ == "__main__":
    rate = 0.7  # requests per second
    T = 60      # total time in seconds
    endpoint = "http://localhost:5000/run-fire-detector"  # target endpoint
 
    load_test(rate, T, endpoint)
