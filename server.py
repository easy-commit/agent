import os
from flask import Flask, jsonify, request
from git import Repo

from generate_commit import generate_commit_messages

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"

app = Flask(__name__)

def get_last_commits(repo_path, n=10):
    try:
        repo = Repo(repo_path)
        return "\n".join(
            commit.message.strip()
            for commit in repo.iter_commits('HEAD', max_count=n)
        )
    except Exception as e:
        print(f"[WARNING] Could not get last commits from {repo_path}: {e}")
        return ""

@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    diff_clean = data.get("diff", "")
    repo_path = data.get("repo_path", None)

    if not repo_path:
        return jsonify({"error": "No repo_path provided in request."}), 400

    repo_commit_examples = get_last_commits(repo_path, 10)
    messages = generate_commit_messages(diff_clean, repo_commit_examples)
    return jsonify({"suggestions": messages})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
