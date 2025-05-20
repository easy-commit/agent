import os
import subprocess
import shutil
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from git import Repo

MODEL_DIR = "./output/commit_model"
TEST_REPO = "/tmp/test-repo"
device = torch.device("cpu")

# Étape 1 : Créer un dépôt temporaire
if os.path.exists(TEST_REPO):
    shutil.rmtree(TEST_REPO)
os.makedirs(TEST_REPO, exist_ok=True)

# Étape 2 : Initialiser le dépôt Git et créer un fichier
repo = Repo.init(TEST_REPO)
with open(os.path.join(TEST_REPO, "hello.py"), "w") as f:
    f.write("print('hello world')\n")

repo.git.add("hello.py")
repo.index.commit("Initial commit")

# Étape 3 : Modifier le fichier
with open(os.path.join(TEST_REPO, "hello.py"), "a") as f:
     f.write("\n\ndef greet(name):\n    print(f\"Hello, {name}\")\n")

repo.git.add("hello.py")

# Étape 4 : Charger le modèle
tokenizer = T5Tokenizer.from_pretrained(MODEL_DIR, legacy=True)
model = T5ForConditionalGeneration.from_pretrained(MODEL_DIR).to(device)

# Étape 5 : Générer le message de commit
diff = repo.git.diff('--cached', '--no-color')
diff_clean = "\n".join(line for line in diff.splitlines() if line.startswith('+') or line.startswith('-'))

if not diff_clean.strip():
    print("[AUCUN CHANGEMENT] Aucun diff détecté.")
else:
    prompt = "Generate a commit message for these changes:\n" + diff_clean
    input_ids = tokenizer(prompt, return_tensors='pt', max_length=512, truncation=True).input_ids.to(device)
    outputs = model.generate(input_ids, max_length=128, num_beams=4, early_stopping=True)
    message = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print("\n💬 Message généré :")
    print(message)