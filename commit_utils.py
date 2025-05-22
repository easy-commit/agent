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

def extract_git_data(repo_path):
    from git import Repo
    repo = Repo(repo_path)
    try:
        branch = repo.active_branch.name
    except Exception:
        branches = [head.name for head in repo.heads]
        if "main" in branches:
            branch = "main"
        elif "master" in branches:
            branch = "master"
        elif branches:
            branch = branches[0]
        else:
            print("[ERROR] No branches found in this repo!")
            return []
    data = []
    for i, commit in enumerate(repo.iter_commits(branch)):
        msg = commit.message.strip()
        if msg.startswith("Merge pull request"):
            continue
        diffs = commit.diff(commit.parents[0] if commit.parents else None, create_patch=True)
        diff_text = ''
        for d in diffs:
            try:
                diff_text += d.diff.decode('utf-8', errors='ignore')
            except Exception:
                continue
        data.append({
            "message": msg,
            "diff": diff_text,
        })
    return data


def prepare_dataset(data):
    return pd.DataFrame(data)

def preprocess_dataset(dataset, tokenizer, max_length=128):
    class CommitDataset(torch.utils.data.Dataset):
        def __init__(self, df):
            self.df = df
            self.inputs = tokenizer(
                list(df['diff']),
                truncation=True,
                padding="max_length",
                max_length=max_length,
                return_tensors="pt"
            )
            self.labels = tokenizer(
                list(df['message']),
                truncation=True,
                padding="max_length",
                max_length=max_length,
                return_tensors="pt"
            )["input_ids"]

        def __len__(self):
            return len(self.df)

        def __getitem__(self, idx):
            input_ids = self.inputs['input_ids'][idx]
            attention_mask = self.inputs['attention_mask'][idx]
            labels = self.labels[idx]
            return {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'labels': labels,
            }
    return CommitDataset(dataset)

def load_urls_from_file(filepath):
    with open(filepath, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls
