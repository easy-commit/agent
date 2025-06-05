import shutil
import tempfile

import pandas as pd
import torch
from git import Repo


def clone_repo_temp(repo_url):
    temp_dir = tempfile.mkdtemp()
    try:
        Repo.clone_from(repo_url, temp_dir)
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


def extract_git_data(repo_path, max_commits=10000):
    print(f"[EXTRACT] Analyzing repository '{repo_path}'")
    repo = Repo(repo_path)
    branches = [
        head.name
        for head in repo.heads
        if not head.name.startswith(("dependabot", "gh-pages"))
    ]
    if not branches:
        print("[ERROR] No branches found in this repo!")
        return []

    total_commits = 0
    for branch in branches:
        count = int(repo.git.rev_list("--count", branch))
        total_commits += count
    total_commits = min(total_commits, max_commits)

    seen_commits = set()
    data = []
    processed = 0
    for branch in branches:
        print(f"[EXTRACT] Analyse de la branche '{branch}'")
        for commit in repo.iter_commits(branch):
            if len(data) >= max_commits:
                print(
                    f"\n[INFO] Limite de {max_commits} commits atteinte, on arrête l'extraction."
                )
                return data
            if commit.hexsha in seen_commits:
                continue
            seen_commits.add(commit.hexsha)
            processed += 1
            percent = (processed / total_commits) * 100
            print(
                f"[EXTRACT] Progress: {percent:.1f}% ({processed}/{total_commits})",
                end="\r",
            )
            msg = commit.message.strip()
            if (
                msg.startswith("Merge pull request")
                or msg.startswith("Merge branch")
                or "pull request" in msg.lower()
            ):
                continue
            diffs = commit.diff(
                commit.parents[0] if commit.parents else None, create_patch=True
            )
            diff_text = ""
            for d in diffs:
                try:
                    diff_text += d.diff.decode("utf-8", errors="ignore")
                except Exception:
                    continue
            data.append(
                {
                    "message": msg,
                    "diff": diff_text,
                }
            )
    print()
    return data


def prepare_dataset(data):
    return pd.DataFrame(data)


def preprocess_dataset(dataset, tokenizer, max_length=128):
    class CommitDataset(torch.utils.data.Dataset):
        def __init__(self, df):
            self.df = df
            self.inputs = tokenizer(
                list(df["diff"]),
                truncation=True,
                padding="max_length",
                max_length=max_length,
                return_tensors="pt",
            )
            self.labels = tokenizer(
                list(df["message"]),
                truncation=True,
                padding="max_length",
                max_length=max_length,
                return_tensors="pt",
            )["input_ids"]

        def __len__(self):
            return len(self.df)

        def __getitem__(self, idx):
            input_ids = self.inputs["input_ids"][idx]
            attention_mask = self.inputs["attention_mask"][idx]
            labels = self.labels[idx]
            return {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }

    return CommitDataset(dataset)


def load_urls_from_file(filepath):
    with open(filepath, "r") as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls
