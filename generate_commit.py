import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

MODEL_OUTPUT_DIR = "output/easycommit_model"
device = torch.device("cpu")

tokenizer = T5Tokenizer.from_pretrained(MODEL_OUTPUT_DIR, legacy=True)
model = T5ForConditionalGeneration.from_pretrained(MODEL_OUTPUT_DIR).to(device)


def generate_commit_messages(diff_clean: str, num_return_sequences: int = 4):
    prompt = "Generate a commit message for these changes:\n" + diff_clean
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
