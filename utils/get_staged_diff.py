from utils.run_git_command import run_git_command

def get_staged_diff(repo_path):
    diff = run_git_command(['git', 'diff', '--cached'], repo_path)
    return diff
