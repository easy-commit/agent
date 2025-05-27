import os
from flask import Flask, jsonify, request
from generate_commit import generate_commit_messages

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"

app = Flask(__name__)

@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    diff_clean = data.get("diff", "")
    messages = generate_commit_messages(diff_clean)
    return jsonify({"suggestions": messages})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
