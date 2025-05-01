import subprocess
import openai

openai.api_key = "TON_API_KEY"

def run_git_command(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout

def get_recent_commit_messages(repo_path, n=10):
    log = run_git_command(['git', 'log', f'-n {n}', '--pretty=format:%s'], repo_path)
    return log.splitlines()

def get_staged_diff(repo_path):
    diff = run_git_command(['git', 'diff', '--cached'], repo_path)
    return diff

def generate_commit_message_with_gpt(commit_messages, staged_diff):
    prompt = f"""Tu es une IA qui aide à écrire des messages de commit clairs et alignés sur les conventions du projet.
Voici des exemples récents :
{chr(10).join(f"- {m}" for m in commit_messages)}

Voici le diff actuel :
{staged_diff}

Génère un message de commit adapté et cohérent avec les exemples."""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )
    return response['choices'][0]['message']['content'].strip()

repo_path = '/chemin/vers/ton/repo'
recent_msgs = get_recent_commit_messages(repo_path)
staged_diff = get_staged_diff(repo_path)
commit_msg = generate_commit_message_with_gpt(recent_msgs, staged_diff)

print("\n✅ Message de commit suggéré :")
print(commit_msg)
