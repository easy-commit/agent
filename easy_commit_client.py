import os
import sys

import requests
from dotenv import load_dotenv
from git import InvalidGitRepositoryError, Repo
from InquirerPy import inquirer

load_dotenv()

API_LINK = os.getenv("API_LINK")
if not API_LINK:
    print("❌ The environment variable API_LINK is not set.")
    print("👉 Example: export API_LINK=192.168.x.x (your server's IP)")
    sys.exit(1)

SERVER_URL = f"http://{API_LINK}:5000/suggest"


def get_repo_diff(repo: Repo) -> str:
    diff = repo.git.diff("--cached", "--no-color")
    if not diff.strip():
        return ""
    return "\n".join(
        line
        for line in diff.splitlines()
        if line.startswith("+") or line.startswith("-")
    )


def get_commit_suggestions(diff_clean: str, repo_path: str) -> list[str]:
    try:
        response = requests.post(
            SERVER_URL,
            json={
                "diff": diff_clean,
                "repo_path": repo_path,
                "num_return_sequences": 6,
            },
        )
        response.raise_for_status()
        return response.json().get("suggestions", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ API error: {e}")
        return []


def commit_with_message(repo_path: str, message: str) -> None:
    try:
        repo = Repo(repo_path)
        repo.git.commit("-m", message)
        print("✅ Commit successful.")
    except Exception as e:
        print(f"❌ Failed to commit: {e}")


def main():
    repo_path = input("📂 Path to the Git repository: ").strip()
    if not repo_path:
        print("❌ No path provided.")
        return

    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        print("❌ Invalid Git repository.")
        return
    except Exception as e:
        print(f"❌ Unexpected error opening repo: {e}")
        return

    diff_clean = get_repo_diff(repo)
    if not diff_clean:
        print("ℹ️ No staged changes detected.")
        return

    suggestions = get_commit_suggestions(diff_clean, repo_path)
    if not suggestions:
        print("❌ No suggestions received from the server.")
        return

    selected = inquirer.select(
        message="💬 Select the commit message:",
        choices=suggestions,
        pointer="👉",
    ).execute()

    print(f"\n✅ Selected message:\n{selected}\n")
    commit_with_message(repo_path, selected)


if __name__ == "__main__":
    main()
