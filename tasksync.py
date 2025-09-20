import prompts
from cerebras_connector import send_message
import json
from github_connector import list_repos, get_branches, get_commits, get_commit_diff, get_diff_between_commits


def extract_tasks(transcript: str) -> list:
    response = send_message(transcript, prompts.TRANSCRIPT_ANALYSIS_PROMPT)
    try:
        tasks = json.loads(response)
        return tasks
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        print("Response was:", response)
        return []


def get_progress(task_title: str, task_description: str, commit_diffs: list) -> str:
    response = send_message(
        message=json.dumps(commit_diffs),
        system_prompt=prompts.COMMIT_ANALYSIS_PROMPT.format(
            task_title=task_title,
            task_description=task_description
        )
    )
    try:
        progress = json.loads(response)
        return progress
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        print("Response was:", response)
        return {}    
    
def get_pretty_diff(token:str, owner:str, repo:str, selected_base_commit:str, selected_head_commit:str) -> list:
    commit_diff = get_diff_between_commits(token, owner, repo, selected_base_commit, selected_head_commit)
    diffs_pretty = []
    for diff in commit_diff.get('files', []): 
        diffs_pretty.append({
            "filename": diff['filename'],
            "patch": diff['patch']
        })
    return diffs_pretty

def test(token:str):
    print("Pick a repo to analyze:")
    repos = list_repos(token)
    for i, repo in enumerate(repos):
        print(f"{i + 1}. {repo['full_name']}")
    repo_choice = int(input("Enter the number of the repo: ")) - 1
    selected_repo = repos[repo_choice]
    owner = selected_repo['owner']['login']
    repo_name = selected_repo['name']
    print(f"Selected repo: {owner}/{repo_name}")
    branches = get_branches(token, owner, repo_name)
    print("Pick a branch to analyze:")
    for i, branch in enumerate(branches):
        print(f"{i + 1}. {branch['name']}")
    branch_choice = int(input("Enter the number of the branch: ")) - 1
    selected_branch = branches[branch_choice]['name']
    print(f"Selected branch: {selected_branch}")
    commits = get_commits(token, owner, repo_name, selected_branch)
    for i, commit in enumerate(commits):
        print(f"{i + 1}. {commit['sha']} - {commit['commit']['message']}")
    base_commit_choice = int(input("Enter the base commit: ")) - 1
    head_commit_choice = int(input("Enter the head commit: ")) - 1
    selected_base_commit = commits[base_commit_choice]['sha']
    selected_head_commit = commits[head_commit_choice]['sha']
    print(f"Selected base commit: {selected_base_commit}")
    print(f"Selected head commit: {selected_head_commit}")
    diffs_pretty = get_pretty_diff(token, owner, repo_name, selected_base_commit, selected_head_commit)

    print("Progress on tasks: ", get_progress("Creating OOP Sample", "Create a Person class with name, email and github username. Create a Pet class with name, species and owner. Create a Dog class that inherits from Pet and has a breed attribute and a bark method.", diffs_pretty))
