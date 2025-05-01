from utils.run_git_command import run_git_command

def get_recent_commit_messages(repo_path, n=10):
    log = run_git_command(['git', 'log', f'-n {n}', '--pretty=format:%s'], repo_path)
    return log.splitlines()
