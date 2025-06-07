import gc
import json
import os
import shutil
import time
from datetime import datetime

import psutil
import torch
from transformers import (T5ForConditionalGeneration, T5Tokenizer, Trainer,
                          TrainingArguments)

from commit_utils import (clone_repo_temp, extract_git_data, prepare_dataset,
                          preprocess_dataset)
from fetch_github import fetch_public_github_repos

os.environ["OMP_NUM_THREADS"] = "6"
os.environ["MKL_NUM_THREADS"] = "6"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"

torch.set_num_threads(6)
torch.set_num_interop_threads(6)
device = torch.device("cpu")

MODEL_NAME = "t5-base"
MODEL_OUTPUT_DIR = "./output/easycommit_model"
CHECKPOINT_DIR = os.path.join(MODEL_OUTPUT_DIR, "checkpoints")
URLS_FILE = "urls-github.json"
DEFAULT_MAX_COMMITS = 10000
DIFF_CHAR_LIMIT = 2000
CPU_USAGE_LIMIT = 80  # percent
MONITOR_FILE = "./training_log.csv"

os.makedirs(CHECKPOINT_DIR, exist_ok=True)


def load_done_urls():
    if os.path.isfile(URLS_FILE):
        with open(URLS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_done_urls(done_urls):
    with open(URLS_FILE, "w") as f:
        json.dump(list(done_urls), f, indent=2)


def limit_cpu_usage():
    """Pause if CPU usage is too high."""
    while psutil.cpu_percent(interval=1) > CPU_USAGE_LIMIT:
        print("[WAIT] CPU usage high. Waiting...")
        time.sleep(5)


def score_commit_message(msg: str) -> float:
    """
    Heuristic score to evaluate commit message quality.
    """
    score = 1.0
    if len(msg) > 100:
        score -= 0.5
    if not any(msg.startswith(prefix) for prefix in ["feat", "fix", "chore", "docs", "refactor", "style", "deps"]):
        score -= 0.3
    if ":" not in msg:
        score -= 0.2
    return max(0.0, score)


def validate_dataset(dataset):
    return [entry for entry in dataset if score_commit_message(entry["message"]) >= 0.5]


def get_training_args(batch_size):
    return TrainingArguments(
        output_dir=MODEL_OUTPUT_DIR,
        num_train_epochs=1,
        per_device_train_batch_size=batch_size,
        save_strategy="no",
        logging_dir="./logs",
        logging_steps=10,
        learning_rate=5e-5,
        weight_decay=0.01,
        use_cpu=True,
        dataloader_num_workers=6,
    )


def train_model_on_dataset(model, dataset):
    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"[INFO] Detected RAM: {ram_gb:.2f} GB")

    if ram_gb > 24:
        batch_size = 16
        max_commits = DEFAULT_MAX_COMMITS
    elif ram_gb > 16:
        batch_size = 8
        max_commits = min(DEFAULT_MAX_COMMITS, 5000)
    else:
        batch_size = 4
        max_commits = min(DEFAULT_MAX_COMMITS, 2000)

    trainer = Trainer(
        model=model,
        args=get_training_args(batch_size),
        train_dataset=dataset,
    )

    print(f"[INFO] Batch size: {batch_size}, Max commits: {max_commits}")
    trainer.train()
    return max_commits


def truncate_diff(data, limit):
    for entry in data:
        if len(entry["diff"]) > limit:
            entry["diff"] = entry["diff"][:limit] + "\n[...truncated...]"
    return data


def log_monitor(repo_url, dataset_size, valid_count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(MONITOR_FILE, "a") as f:
        f.write(f"{now},{repo_url},{dataset_size},{valid_count}\n")


def load_latest_model_or_base():
    latest_checkpoints = sorted(
        [os.path.join(CHECKPOINT_DIR, d) for d in os.listdir(CHECKPOINT_DIR)
         if os.path.isdir(os.path.join(CHECKPOINT_DIR, d))],
        reverse=True
    )

    if latest_checkpoints:
        last_checkpoint = latest_checkpoints[0]
        print(f"[INFO] Resuming model from last checkpoint: {last_checkpoint}")
        tokenizer = T5Tokenizer.from_pretrained(last_checkpoint, legacy=True)
        model = T5ForConditionalGeneration.from_pretrained(last_checkpoint).to(device)
    else:
        print(f"[INFO] No checkpoint found. Initializing model from base: {MODEL_NAME}")
        tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME, legacy=True)
        model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)
    return tokenizer, model


if not os.path.exists(MONITOR_FILE):
    os.makedirs(os.path.dirname(MONITOR_FILE), exist_ok=True)
    with open(MONITOR_FILE, "w") as f:
        f.write("timestamp,repo_url,total_samples,valid_samples\n")

if __name__ == "__main__":

    done_urls = load_done_urls()
    print(f"[INFO] {len(done_urls)} repositories already processed.")

    tokenizer, model = load_latest_model_or_base()

    while True:
        urls = fetch_public_github_repos(per_page=100, pages=1)
        print(f"[INFO] {len(urls)} new repositories fetched.")

        new_urls = [url for url in urls if url not in done_urls]
        print(f"[INFO] {len(new_urls)} repositories to process.")

        if not new_urls:
            print("[INFO] No new repositories. Sleeping for 1 hour...")
            time.sleep(3600)
            continue

        for i, repo_url in enumerate(new_urls, start=1):
            limit_cpu_usage()

            repo_name = repo_url.rstrip("/").split("/")[-1]
            print(f"\n🧠 [{i}/{len(new_urls)}] Processing: {repo_url}")
            temp_repo_path = None

            try:
                temp_repo_path = clone_repo_temp(repo_url)
                data = extract_git_data(temp_repo_path, max_commits=DEFAULT_MAX_COMMITS)

                if not data:
                    print(f"[SKIP] No valid commits.")
                    continue

                data = truncate_diff(data, DIFF_CHAR_LIMIT)
                data = validate_dataset(data)

                if len(data) < 10:
                    print(f"[SKIP] Not enough valid data after validation.")
                    continue

                dataset = prepare_dataset(data)
                tokenized = preprocess_dataset(dataset, tokenizer)

                print(f"[INFO] Dataset: {len(data)} entries after validation.")

                train_model_on_dataset(model, tokenized)

                model.save_pretrained(MODEL_OUTPUT_DIR)
                tokenizer.save_pretrained(MODEL_OUTPUT_DIR)

                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                version_path = os.path.join(CHECKPOINT_DIR, f"{timestamp}_{repo_name}")
                model.save_pretrained(version_path)
                tokenizer.save_pretrained(version_path)

                log_monitor(repo_url, len(data), len(data))

            except Exception as e:
                print(f"[ERROR] {repo_url}: {e}")

            finally:
                if temp_repo_path:
                    shutil.rmtree(temp_repo_path, ignore_errors=True)
                done_urls.add(repo_url)
                save_done_urls(done_urls)
                try:
                    del dataset, tokenized
                except:
                    pass
                gc.collect()
                try:
                    torch.cuda.empty_cache()
                except:
                    pass

        print("\n✅ All repositories processed. Sleeping for 10 minutes...")
        time.sleep(600)
