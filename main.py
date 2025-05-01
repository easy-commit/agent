from utils.generate_commit_message_with_gpt import generate_commit_message_with_gpt
from utils.get_recent_commit_messages import get_recent_commit_messages
from utils.get_staged_diff import get_staged_diff

repo_path = input('Enter repo relative path: ')
recent_msgs = get_recent_commit_messages(repo_path)
staged_diff = get_staged_diff(repo_path)
commit_msg = generate_commit_message_with_gpt(recent_msgs, staged_diff)

print("\nmessage de commit suggéré :")
print(commit_msg)
