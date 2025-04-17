from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

APP1_URL = os.getenv("APP1_URL", "http://flask-app-1-service:5000")
APP2_URL = os.getenv("APP2_URL", "http://flask-app-2-service:5000")

@app.route('/health')
def health():
    return jsonify({"status": "Gateway is running"})

@app.route('/run-fire-detector', methods=['POST'])
def gateway():
    try:
        app1_response = requests.post(f"{APP1_URL}/run-fire-detector")
        app1_data = app1_response.json()
        
        app2_response = requests.post(
            f"{APP2_URL}/run-fire-detector-2",
            json=app1_data
        )
        
        return jsonify(app2_response.json())
        
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Gateway request failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5050))
    app.run(host='0.0.0.0', port=port)
