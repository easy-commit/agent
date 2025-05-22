import json
import os
import shutil
import time

import psutil
import torch
from transformers import (T5ForConditionalGeneration, T5Tokenizer, Trainer,
                          TrainingArguments)

from commit_utils import (clone_repo_temp, extract_git_data, prepare_dataset,
                          preprocess_dataset)
from fetch_github import fetch_public_github_repos

MODEL_NAME = "t5-base"
MODEL_OUTPUT_DIR = "./output/easycommit_model"
URLS_FILE = "urls-github.json"

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"
device = torch.device("cpu")


def load_done_urls():
    if os.path.isfile(URLS_FILE):
        with open(URLS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_done_urls(done_urls):
    with open(URLS_FILE, "w") as f:
        json.dump(list(done_urls), f, indent=2)


def train_model_on_dataset(model, dataset):
    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"[INFO] Detected RAM: {ram_gb:.2f} GB")
    if ram_gb > 24:
        batch_size = 16
    elif ram_gb > 16:
        batch_size = 8
    else:
        batch_size = 4

    training_args = TrainingArguments(
        output_dir=MODEL_OUTPUT_DIR,
        num_train_epochs=1,
        per_device_train_batch_size=batch_size,
        save_strategy="epoch",
        save_total_limit=2,
        logging_dir="./logs",
        logging_steps=10,
        learning_rate=5e-5,
        weight_decay=0.01,
        use_cpu=True,
        resume_from_checkpoint=os.path.isdir(
            os.path.join(MODEL_OUTPUT_DIR, "checkpoint-1")
        ),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )
    print(f"[INFO] Batch size used: {batch_size}")
    trainer.train(resume_from_checkpoint=training_args.resume_from_checkpoint)


if __name__ == "__main__":
    if os.path.isdir(MODEL_OUTPUT_DIR):
        print("[INFO] Loading existing trained model.")
        tokenizer = T5Tokenizer.from_pretrained(MODEL_OUTPUT_DIR, legacy=True)
        model = T5ForConditionalGeneration.from_pretrained(MODEL_OUTPUT_DIR).to(device)
    else:
        print(f"[INFO] Loading base model {MODEL_NAME}.")
        tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME, legacy=True)
        model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)

    done_urls = load_done_urls()
    print(f"[INFO] {len(done_urls)} repos already processed.")

    while True:
        urls = fetch_public_github_repos(per_page=100, pages=1)
        print(f"[INFO] {len(urls)} new repos found automatically.")

        new_urls = [url for url in urls if url not in done_urls]
        print(f"[INFO] {len(new_urls)} repos to process (not yet seen).")

        if not new_urls:
            print(
                "[INFO] No new repos to process. Pausing for 1 hour before retrying..."
            )
            time.sleep(3600)
            continue

        for i, repo_url in enumerate(new_urls, start=1):
            repo_name = repo_url.rstrip("/").split("/")[-1]
            print(f"\n🧠 [Repo {i}/{len(new_urls)}] {repo_url}")
            print(f"[CLONE] Cloning repo '{repo_name}' ({repo_url})")
            temp_repo_path = None
            try:
                temp_repo_path = clone_repo_temp(repo_url)
                data = extract_git_data(temp_repo_path)
                if not data or len(data) == 0:
                    print(f"[SKIP] No usable commits in {repo_url}")
                else:
                    dataset = prepare_dataset(data)
                    tokenized = preprocess_dataset(dataset, tokenizer)
                    train_model_on_dataset(model, tokenized)
            except Exception as e:
                print(f"[ERROR] Problem with {repo_url}: {e}")
            finally:
                if temp_repo_path:
                    shutil.rmtree(temp_repo_path, ignore_errors=True)
                done_urls.add(repo_url)
                save_done_urls(done_urls)

        print("\n✅ End of loop. Saving the model...")
        model.save_pretrained(MODEL_OUTPUT_DIR)
        tokenizer.save_pretrained(MODEL_OUTPUT_DIR)
        print("[INFO] Pausing for 10 minutes before fetching new repositories...")
        time.sleep(600)
