from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/', methods=['GET'])
def health():
    """
    Health check endpoint to verify the API is running.
    Returns a status message.
    """
    return jsonify({
        "status": "ok",
        "message": "RL agent API is running"
    })

@app.route('/action', methods=['POST'])
def action():
    """
    Receive training data and return a random decision.
    Expected body format:
    {
        "observation": {
            "n_instances": int,
            "workload": float,
            "utilization": float,
            "pressure": float,
            "queue_length_dominant": float
        }
    }

    Returns a random number between 1-3
    """
    data = request.json
    observation = data.get("observation", {})
    if not observation:
        return jsonify({
            "error": "Missing observation data"
        }), 400
    required_fields = ["workload", "utilization", "pressure", "queue_length_dominant"]
    missing_fields = [field for field in required_fields if field not in observation]
    
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    decision = random.randint(1, 3)

    return jsonify({
        "action": decision,
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
