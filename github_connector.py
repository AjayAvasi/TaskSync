import requests


def list_repos(token: str) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.github.com/user/repos", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching repositories: {response.status_code} - {response.text}")

def get_branches(token: str, owner: str, repo: str) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching branches: {response.status_code} - {response.text}")

def get_commits(token: str, owner: str, repo: str, branch: str) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching commits: {response.status_code} - {response.text}")
    
def get_commit_diff(token: str, owner: str, repo: str, commit_sha: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching commit diff: {response.status_code} - {response.text}")

def create_issue(token: str, owner: str, repo: str, title: str, body: str, assignees: list) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data = {
        "title": title,
        "body": body,
        "assignees": assignees
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Error creating issue: {response.status_code} - {response.text}")

def get_diff_between_commits(token: str, owner: str, repo: str, base_sha: str, head_sha: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base_sha}...{head_sha}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching diff between commits: {response.status_code} - {response.text}")


