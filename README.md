## Easy commit

Create a model with Deep Learning (supervised) by training it on the repository of your choice (which you'll have locally), giving it the changes as input and the commit message as output.

This allows you to have a model trained with its own context, so it will respect the commit message conventions of the repository with which it has been trained.

### Install dependencies

```bash
pip install -r requirements.txt
```

### Train the model

```bash
python main.py
>> Do you want to generate a commit message or to train the model on a specific repository ?:
[train/generate] : train
>> Enter the path to the repository you want to train on:
/path/to/your/repo
```
And it will start training the model on the repository you provided. It will take a while depending on the size of the repository and the number of commits it has.

### Generate a commit message

```bash
python main.py
>> Do you want to generate a commit message or to train the model on a specific repository ?:
[train/generate] : generate
>> Enter the path to the repository you want to generate a commit message for:
/path/to/your/repo
```
And it will generate a commit message for the repository you provided based on the staged changes.
