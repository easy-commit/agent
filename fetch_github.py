import os
import requests
import time

def fetch_public_github_repos(per_page=20, pages=2):
    url = "https://api.github.com/search/repositories"
    token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github+json",
    }

    if token:
        headers["Authorization"] = f"token {token}"
    else:
        print("⚠️ No GitHub token detected. You are limited to 60 requests per hour.")

    all_repos = []
    for page in range(1, pages + 1):
        params = {
            "q": "stars:>10 pushed:>2024-01-01",
            "sort": "updated",
            "order": "desc",
            "per_page": per_page,
            "page": page,
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 403:
            print("❌ GitHub API rate limit exceeded.")
            if not token:
                print("💡 Use a GitHub token to increase your rate limit to 5000 requests/hour.")
                print("🔗 Create one here: https://github.com/settings/tokens")
            else:
                print("🔐 Your token may have reached its limit or is invalid.")
            exit(1)

        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])
        all_repos += [repo["clone_url"] for repo in items]

        time.sleep(1)

    return all_repos
