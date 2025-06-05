import re

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

MODEL_OUTPUT_DIR = "output/easycommit_model"
device = torch.device("cpu")

tokenizer = T5Tokenizer.from_pretrained(MODEL_OUTPUT_DIR, legacy=True)
model = T5ForConditionalGeneration.from_pretrained(MODEL_OUTPUT_DIR).to(device)


def is_valid_commit(msg: str) -> bool:
    pattern = r"^(feat|fix|docs|refactor|chore|style|deps)(\([^)]+\))?:\s.+"
    return bool(re.match(pattern, msg)) and len(msg) <= 70


def truncate(text, max_chars):
    if len(text) > max_chars:
        return text[:max_chars] + "\n[...truncated...]"
    return text


def generate_commit_messages(
    diff_clean: str, repo_commit_examples: str = "", num_return_sequences: int = 4
) -> list[str]:
    repo_commit_examples = truncate(repo_commit_examples, 1200)
    diff_clean = truncate(diff_clean, 1200)

    prompt = (
        f"You are an expert software engineer and git user. "
        f"Your task is to generate {num_return_sequences} unique, high-quality, and concise commit messages for the following code changes (the diff below). "
        "Each message must follow these rules:\n"
        "- Strictly use the Conventional Commits format (`feat:`, `fix:`, `chore:`, `refactor:`, `style:`, `docs:`, `deps:` etc.)\n"
        "- Keep every message very short and to the point (preferably one line, ideally less than 70 characters)\n"
        "- Avoid unnecessary words or explanations\n"
        "- No full sentences, no justifications—only describe what changed, as briefly as possible\n"
        "- Use a relevant scope (e.g., `feat(api): ...`, `fix(core): ...`) if appropriate\n"
        "- Only use `docs(readme): ...` for README file changes\n"
        "- Never use `docs(readme):` for other files\n"
        "- Adapt your style and tone to match the previous commits (see below)\n"
        "- If you are unsure, make a best guess but keep it brief and conventional\n"
        "- Number each suggestion\n"
        "\n"
        "Below are sample commit messages from this project's history for style reference:\n"
        f"{repo_commit_examples if repo_commit_examples else '[No previous commit in repo]'}\n"
        "\n"
        "Here is the staged diff:\n"
        f"{diff_clean}\n"
        "\n"
        "Now, generate the commit messages:"
    )

    input_ids = tokenizer(
        prompt, return_tensors="pt", max_length=512, truncation=True
    ).input_ids.to(device)

    outputs = model.generate(
        input_ids,
        max_length=128,
        num_beams=num_return_sequences,
        early_stopping=True,
        num_return_sequences=num_return_sequences,
        use_cache=False,
    )

    raw_messages = [
        tokenizer.decode(output, skip_special_tokens=True).strip() for output in outputs
    ]

    valid_messages = [msg for msg in raw_messages if is_valid_commit(msg)]

    if not valid_messages:
        print("[❌] Aucun message valide généré ! Messages bruts :")
        for i, msg in enumerate(raw_messages, 1):
            print(f"{i}. {msg}")
        raise ValueError("No valid commit message could be generated.")

    valid_messages.sort(key=len)

    return valid_messages
