import os
import torch
from git import Repo
from transformers import T5ForConditionalGeneration, T5Tokenizer

MODEL_OUTPUT_DIR = "output/easycommit_model"

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"
device = torch.device('cpu')

if __name__ == "__main__":
    repo_path = input("Chemin du repo Git pour générer un message de commit : ").strip()

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
