import os
import sys
import json
import tempfile
import shutil
from git import Repo
from tqdm import tqdm
from transformers import T5ForConditionalGeneration, T5Tokenizer, Trainer, TrainingArguments
from datasets import Dataset
import torch
import psutil

MODEL_NAME = "t5-small"
MODEL_OUTPUT_DIR = "./output/commit_model"

# Force CPU usage
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"

device = torch.device('cpu')

if os.environ.get('TERM'):
    os.system('cls' if os.name == 'nt' else 'clear')

def extract_git_data(repo_path, max_commits=None):
    repo = Repo(repo_path)
    try:
        branch_name = repo.active_branch.name
    except TypeError:
        branch_name = repo.git.rev_parse('--abbrev-ref', 'HEAD')
    commits = [c for c in repo.iter_commits(branch_name) if not c.message.lower().startswith('merge pull request')]
    data = []
    for commit in tqdm(commits[:max_commits]):
        diff = repo.git.show(commit.hexsha, '--no-color')
        message = commit.message.strip()
        data.append({'diff': diff, 'message': message})
    return data

def prepare_dataset(data):
    diffs = [item['diff'] for item in data]
    messages = [item['message'] for item in data]
    return Dataset.from_dict({'diff': diffs, 'message': messages})

def preprocess_dataset(dataset, tokenizer):
    def preprocess(examples):
        diffs_cleaned = []
        for diff in examples['diff']:
            lines = [line for line in diff.splitlines() if line.startswith('+') or line.startswith('-')]
            diffs_cleaned.append("\n".join(lines))

        inputs = ["Generate a commit message for these changes:\n" + d for d in diffs_cleaned]
        model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding='max_length')

        labels = tokenizer(examples['message'], max_length=64, truncation=True, padding='max_length')
        label_ids = labels['input_ids']
        label_ids = [[token if token != tokenizer.pad_token_id else -100 for token in l] for l in label_ids]

        model_inputs['labels'] = label_ids
        return model_inputs

    return dataset.map(preprocess, batched=True, load_from_cache_file=False, keep_in_memory=True)

def train_model_on_dataset(model, _, dataset):
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    print(f"[INFO] RAM détectée : {ram_gb:.2f} GB")
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
        logging_dir='./logs',
        logging_steps=10,
        learning_rate=5e-5,
        weight_decay=0.01,
        use_cpu=True,
        resume_from_checkpoint=os.path.isdir(os.path.join(MODEL_OUTPUT_DIR, 'checkpoint-1'))
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )

    print(f"[INFO] Batch size utilisé : {batch_size}")
    trainer.train(resume_from_checkpoint=training_args.resume_from_checkpoint)

def clone_repo_temp(url):
    temp_dir = tempfile.mkdtemp(prefix="repo_")
    print(f"[INFO] Clonage du dépôt dans {temp_dir}")
    try:
        Repo.clone_from(url, temp_dir)
    except Exception as e:
        print(f"[ERREUR] Échec du clonage de {url} : {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return temp_dir

def load_urls_from_file(filepath):
    if filepath.endswith('.json'):
        with open(filepath, 'r', encoding='utf-8') as f:
            urls = json.load(f)
    elif filepath.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        raise ValueError("Format non supporté. Utilise un fichier .json ou .txt")
    return urls

if __name__ == "__main__":
    mode = input("Mode :\n[multi-url/generate] : ").strip()

    if mode == "multi-url":
        urls_file = input("Chemin vers le fichier contenant les URLs : ").strip()
        if os.environ.get('TERM'):
            os.system('cls' if os.name == 'nt' else 'clear')
        urls = load_urls_from_file(urls_file)

        if os.path.isdir(MODEL_OUTPUT_DIR):
            print("[INFO] Chargement du modèle entraîné existant.")
            tokenizer = T5Tokenizer.from_pretrained(MODEL_OUTPUT_DIR, legacy=True)
            model = T5ForConditionalGeneration.from_pretrained(MODEL_OUTPUT_DIR).to(device)
        else:
            print(f"[INFO] Chargement du modèle de base {MODEL_NAME}.")
            tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME, legacy=True)
            model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)

        for i, repo_url in enumerate(urls, start=1):
            print(f"\n🧠 [Repo {i}/{len(urls)}] {repo_url}")
            temp_repo_path = None
            try:
                temp_repo_path = clone_repo_temp(repo_url)
                data = extract_git_data(temp_repo_path, max_commits=500)
                dataset = prepare_dataset(data)
                tokenized = preprocess_dataset(dataset, tokenizer)
                train_model_on_dataset(model, None, tokenized)
            except Exception as e:
                print(f"[ERREUR] Problème avec {repo_url} : {e}")
            finally:
                if temp_repo_path:
                    shutil.rmtree(temp_repo_path, ignore_errors=True)

        print("\n✅ Entraînement terminé. Sauvegarde du modèle...")
        model.save_pretrained(MODEL_OUTPUT_DIR)
        tokenizer.save_pretrained(MODEL_OUTPUT_DIR)

    elif mode == "generate":
        repo_path = input("Chemin du repo Git pour générer un message de commit : ").strip()
        if os.environ.get('TERM'):
            os.system('cls' if os.name == 'nt' else 'clear')

        tokenizer = T5Tokenizer.from_pretrained(MODEL_OUTPUT_DIR, legacy=True)
        model = T5ForConditionalGeneration.from_pretrained(MODEL_OUTPUT_DIR).to(device)

        repo = Repo(repo_path)
        diff = repo.git.diff('--cached', '--no-color')

        if not diff.strip():
            print("[AUCUN CHANGEMENT] Aucun fichier en staging.")
        else:
            diff_clean = "\n".join(line for line in diff.splitlines() if line.startswith('+') or line.startswith('-'))
            prompt = "Generate a commit message for these changes:\n" + diff_clean
            input_ids = tokenizer(prompt, return_tensors='pt', max_length=512, truncation=True).input_ids.to(device)
            outputs = model.generate(input_ids, max_length=128, num_beams=4, early_stopping=True, use_cache=False)
            message = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"\n💬 Suggestion de commit : {message}")

    else:
        print("[ERREUR] Mode non reconnu.")