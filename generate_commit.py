import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

MODEL_OUTPUT_DIR = "output/easycommit_model"
device = torch.device("cpu")

tokenizer = T5Tokenizer.from_pretrained(MODEL_OUTPUT_DIR, legacy=True)
model = T5ForConditionalGeneration.from_pretrained(MODEL_OUTPUT_DIR).to(device)


def generate_commit_messages(diff_clean: str, num_return_sequences: int = 4):
    prompt = (
        f"You are an expert software engineer and git user. Your task is to generate {num_return_sequences} unique and high-quality commit messages for the following code changes. "
        "Each message should be written in a different style or focus, such as: "
        "1. Concise summary (max 10 words), "
        "2. Detailed explanation (include what and why), "
        "3. Bugfix style (if applicable, mention the bug and fix), "
        "4. Feature addition (if applicable, describe the new feature), "
        "5. Conventional commit style (e.g., feat:, fix:, chore:), "
        "6. Imperative mood, "
        "7. With context for reviewers, "
        "8. With a call to action or next steps. "
        "Number each message and avoid repetition. "
        "Use the Conventional Commits format (e.g., feat:, fix:, chore:, refactor:, docs:, etc.) whenever possible. "
        "Below are some example commit messages from this project. "
        "Please write new messages that match their style and tone as closely as possible: "
        "- feat(api): add user authentication and JWT support\n"
        "- fix(auth): correct password validation logic\n"
        "- chore(deps): update lodash to latest version\n"
        "- refactor(core): simplify data fetching in Home component\n"
        "- docs(readme): clarify setup instructions\n"
        "If the diff is unclear, make a best guess based on the changes. "
        "DIFF:\n" + diff_clean
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
    messages = [
        tokenizer.decode(output, skip_special_tokens=True) for output in outputs
    ]
    return messages
