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
    print("❌ La variable d'environnement API_LINK n'est pas définie.")
    print("Exemple : export API_LINK=192.168.x.x (IP de ton serveur)")
    sys.exit(1)

SERVER_URL = f"http://{API_LINK}:5000/suggest"


def main():
    repo_path = input(
        "Chemin du dépôt Git pour générer un message de commit : "
    ).strip()
    if not repo_path:
        print("❌ Chemin non renseigné.")
        return

    try:
        repo = Repo(repo_path)
    except Exception as e:
        print(f"❌ Impossible d'ouvrir le dépôt : {e}")
        return

    diff = repo.git.diff("--cached", "--no-color")
    if not diff.strip():
        print("🔹 Aucun fichier n'est indexé (staged).")
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
        print(f"❌ Impossible de joindre le serveur API : {e}")
        return

    suggestions = response.json().get("suggestions", [])
    if not suggestions:
        print("❌ Pas de suggestions reçues du serveur.")
        return

    selected = inquirer.select(
        message="💬 Sélectionne le message de commit à utiliser :",
        choices=suggestions,
        pointer="👉",
    ).execute()

    print(f"\n✅ Message sélectionné :\n{selected}\n")

    try:
        subprocess.run(["git", "-C", repo_path, "commit", "-m", selected], check=True)
        print("🚀 Commit effectué avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du commit : {e}")


if __name__ == "__main__":
    main()
