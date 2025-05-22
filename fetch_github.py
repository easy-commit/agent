import requests

def fetch_public_github_repos(per_page=20, pages=2):
    url = "https://api.github.com/search/repositories"
    all_repos = []
    for page in range(1, pages + 1):
        params = {
            "q": "stars:>100",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        all_repos += [repo["clone_url"] for repo in items]
    return all_repos
