from flask import Flask, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)

# Allow ALL domains (or allow specific one)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Predefined response types ---
RESPONSES = [
    {
        "type": "bar",
        "data": [
            {"label": "India", "value": "25"},
            {"label": "America", "value": "29"},
            {"label": "Africa", "value": "21"}
        ],
        "explanation": "Sample bar chart explanation.",
        "customer_specific": "False",
        "query_executed":"sajdbasjc"
    },
    {
        "type": "text",
        "data": "123",
        "explanation": "Sample scVCAHSVBCHJBSACalar explanation.",
        "customer_specific": "False",
        "query_executed":"sajdbasjc"
    },
    {
        "type": "text",
        "data": {
            "name": "sample_name",
            "age": "23",
            "state": "sample_state",
            "cif_no":"CIF100000",
            "asjahbcjasc":"ajsbcjkacs",
            "asjcbjhsabc":"askjbckjabsc",
            "akjscbkjasbc":"akjsbckjacs"
        },
        "explanation": "Sample object explanation.",
        "customer_specific": "True",
        "query_executed":"sajdbasjc"
    }
]

@app.route("/query", methods=["POST"])
def handle_query():
    payload = request.get_json()
    user_query = payload.get("user_query", "")
    user_id = payload.get("user_id", "unknown")
    
    print(f"Query from user '{user_id}': {user_query}")
    
    # random pick — no if/else
    return jsonify(random.choice(RESPONSES))

@app.route("/users", methods=["POST"])
def get_users():
    payload = request.get_json()
    user_id = payload.get("user_id", "unknown")
    
    print(f"Fetching users for: {user_id}")
    
    # Return sample user data
    # Replace this with your actual database query
    return jsonify({
        "status": "ok",
        "rows": [
            {
                "CIF_NO": "CIF200000",
                "CUSTOMER_NAME": "Sample Customer 1",
                "MOBILE_PHONE": "+1 555-0001",
                "EMAIL_ADDRESS": "customer1@example.com"
            },
            {
                "CIF_NO": "CIF200001",
                "CUSTOMER_NAME": "Sample Customer 2",
                "MOBILE_PHONE": "+1 555-0002",
                "EMAIL_ADDRESS": "customer2@example.com"
            }
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
