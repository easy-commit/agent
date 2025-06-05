import json
import os
import subprocess

import pandas as pd
from flask import (Flask, jsonify, redirect, render_template_string, request,
                   send_file, url_for)
from git import Repo

from generate_commit import generate_commit_messages

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"

app = Flask(__name__)
MONITOR_FILE = "./training_log.csv"
URLS_FILE = "urls-github.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>EasyCommit Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f5f5f5; }
        .stats { margin-top: 10px; font-size: 1.1em; }
        .actions { margin-top: 20px; }
        button { padding: 10px 20px; font-size: 1em; margin-right: 10px; }
    </style>
</head>
<body>
    <h1>EasyCommit Training Dashboard</h1>
    <div class=\"stats\">
        <p><strong>Total Repositories:</strong> {{ stats.total }}</p>
        <p><strong>Processed:</strong> {{ stats.done }}</p>
        <p><strong>Remaining:</strong> {{ stats.pending }}</p>
    </div>
    <div class=\"actions\">
        <form method=\"POST\" action=\"/trigger-training\">
            <button type=\"submit\">🔁 Trigger Training</button>
        </form>
        <form method=\"GET\" action=\"/export\">
            <button type=\"submit\">📄 Export CSV</button>
        </form>
    </div>
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Repository</th>
                <th>Total Samples</th>
                <th>Valid Samples</th>
            </tr>
        </thead>
        <tbody>
            {% for row in logs %}
            <tr>
                <td>{{ row.timestamp }}</td>
                <td>{{ row.repo_url }}</td>
                <td>{{ row.total_samples }}</td>
                <td>{{ row.valid_samples }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""


def get_last_commits(repo_path, n=10):
    try:
        repo = Repo(repo_path)
        return "\n".join(
            commit.message.strip() for commit in repo.iter_commits("HEAD", max_count=n)
        )
    except Exception as e:
        print(f"[WARNING] Could not get last commits from {repo_path}: {e}")
        return ""


@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    diff_clean = data.get("diff", "")
    repo_path = data.get("repo_path")
    num_return_sequences = data.get("num_return_sequences", 4)

    if not repo_path:
        return jsonify({"error": "No repo_path provided in request."}), 400

    repo_commit_examples = get_last_commits(repo_path, 10)

    try:
        messages = generate_commit_messages(
            diff_clean,
            repo_commit_examples,
            num_return_sequences=int(num_return_sequences),
        )
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 500

    return jsonify({"suggestions": messages})


@app.route("/dashboard")
def dashboard():
    logs = []
    stats = {"total": 0, "done": 0, "pending": 0}
    if os.path.exists(MONITOR_FILE):
        df = pd.read_csv(MONITOR_FILE)
        logs = df.to_dict(orient="records")
    if os.path.exists(URLS_FILE):
        with open(URLS_FILE) as f:
            all_urls = set(json.load(f))
        processed_urls = {row["repo_url"] for row in logs if "repo_url" in row}
        stats["total"] = len(all_urls)
        stats["done"] = len(processed_urls)
        stats["pending"] = max(0, stats["total"] - stats["done"])
    return render_template_string(HTML_TEMPLATE, logs=logs, stats=stats)


@app.route("/export")
def export_csv():
    if os.path.exists(MONITOR_FILE):
        return send_file(MONITOR_FILE, as_attachment=True)
    return "No log file found", 404


@app.route("/trigger-training", methods=["POST"])
def trigger_training():
    try:
        subprocess.Popen(["python3", "train_model.py"])
        return redirect(url_for("dashboard"))
    except Exception as e:
        return f"Error triggering training: {e}", 500


@app.route("/validate", methods=["GET"])
def validate():
    diff_example = """
    diff --git a/app.py b/app.py
    index 83db48e..bf3c32a 100644
    --- a/app.py
    +++ b/app.py
    @@ def hello():
    -    return \"Hello World\"
    +    return \"Hello EasyCommit\"
    """
    try:
        examples = generate_commit_messages(
            diff_example, repo_commit_examples="fix(ui): correct greeting"
        )
        return jsonify({"validation_examples": examples})
    except Exception as e:
        return jsonify({"error": f"Validation failed: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
