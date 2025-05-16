from git import Repo
from tqdm import tqdm
from transformers import T5ForConditionalGeneration, T5Tokenizer, Trainer, TrainingArguments
from datasets import Dataset
import os

def clear_terminal():
	os.system('cls' if os.name == 'nt' else 'clear')

def extract_git_data(repo_path, max_commits=None):
	repo = Repo(repo_path)
	commits = list(repo.iter_commits('main'))
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

def train_model(dataset):
	model_path = './output/commit_model'
	checkpoint_path = os.path.join(model_path, 'checkpoint-last')

	if os.path.isdir(model_path):
		tokenizer = T5Tokenizer.from_pretrained(model_path)
		model = T5ForConditionalGeneration.from_pretrained(model_path)
	else:
		tokenizer = T5Tokenizer.from_pretrained('t5-small')
		model = T5ForConditionalGeneration.from_pretrained('t5-small')

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

	tokenized_datasets = dataset.map(preprocess, batched=True)

	training_args = TrainingArguments(
		output_dir=model_path,
		num_train_epochs=5,
		per_device_train_batch_size=4,
		save_strategy="epoch",
		save_total_limit=3,
		logging_dir='./logs',
		logging_steps=10,
		learning_rate=5e-5,
		weight_decay=0.01
	)

	trainer = Trainer(
		model=model,
		args=training_args,
		train_dataset=tokenized_datasets,
	)

	if os.path.isdir(checkpoint_path):
		trainer.train(resume_from_checkpoint=checkpoint_path)
	else:
		trainer.train()

	model.save_pretrained(model_path)
	tokenizer.save_pretrained(model_path)

def suggest_commit_message(repo_path):
	model_path = os.path.abspath('./output/commit_model')
	tokenizer = T5Tokenizer.from_pretrained(model_path)
	model = T5ForConditionalGeneration.from_pretrained(model_path)
	repo = Repo(repo_path)
	diff = repo.git.diff('--cached', '--no-color')

	if not diff.strip():
		return "[No staged changes]"

	diff_clean = "\n".join(line for line in diff.splitlines() if line.startswith('+') or line.startswith('-'))

	prompt = "Generate a commit message for these changes:\n" + diff_clean
	input_ids = tokenizer(prompt, return_tensors='pt', max_length=512, truncation=True).input_ids
	outputs = model.generate(input_ids, max_length=128, num_beams=4, early_stopping=True)
	message = tokenizer.decode(outputs[0], skip_special_tokens=True)

	return message.strip()

if __name__ == "__main__":
	trainOrGenerate = input("Do you want to generate a commit message or to train the model on a specific repository ?: \n[train/generate] : ")

	if trainOrGenerate == "train":
		repo_path = input("Enter the path to the repository you want to train on: ")
	else:
		repo_path = input("Enter the path to the repository you want to generate a commit message for: ")

	clear_terminal()

	if trainOrGenerate == 'train':
		data = extract_git_data(repo_path, max_commits=500)
		dataset = prepare_dataset(data)
		train_model(dataset)
	else:
		suggestion = suggest_commit_message(repo_path)
		print(f"\n💬 Commit suggestion : {suggestion}")
