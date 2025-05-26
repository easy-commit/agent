import os
import subprocess
import sys

import requests
from dotenv import load_dotenv
from git import Repo
from InquirerPy import inquirer

load_dotenv()

API_LINK = os.getenv("API_LINK")
if not API_LINK:
    print("The environment variable API_LINK is not set.")
    print("Example: export API_LINK=192.168.x.x (your server's IP)")
    sys.exit(1)

SERVER_URL = f"http://{API_LINK}:5000/suggest"


def main():
    repo_path = input(
        "Chemin du dépôt Git pour générer un message de commit : "
    ).strip()
    if not repo_path:
        print("❌ Path not provided.")
        return

    try:
        repo = Repo(repo_path)
    except Exception as e:
        print(f"❌ Unable to open the repository: {e}")
        return

    diff = repo.git.diff("--cached", "--no-color")
    if not diff.strip():
        print("🔹 No files are staged (indexed).")
        return

    diff_clean = "\n".join(
        line
        for line in diff.splitlines()
        if line.startswith("+") or line.startswith("-")
    )

    try:
        response = requests.post(SERVER_URL, json={"diff": diff_clean})
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Unable to reach the API server: {e}")
        return

    suggestions = response.json().get("suggestions", [])
    if not suggestions:
        print("❌ No suggestions received from the server.")
        return

    selected = inquirer.select(
        message="Select the commit message to use:",
        choices=suggestions,
        pointer="👉",
    ).execute()

    print(f"\n✅ Selected message:\n{selected}\n")

    try:
        subprocess.run(["git", "-C", repo_path, "commit", "-m", selected], check=True)
        print("🚀 Commit completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during commit: {e}")


if __name__ == "__main__":
    main()
