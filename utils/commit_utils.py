import requests
from datetime import datetime

class Commit:
    def __init__(self, commit_data):
        self.sha = commit_data['sha']
        self.author_name = commit_data['commit']['author']['name']
        self.author_email = commit_data['commit']['author']['email']
        self.date = datetime.strptime(commit_data['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
        self.message = commit_data['commit']['message']
        self.html_url = commit_data['html_url']

    def __str__(self):
        return f"Commit: {self.sha[:7]}\n" \
               f"Author: {self.author_name} <{self.author_email}>\n" \
               f"Date: {self.date.strftime('%Y-%m-%d %H:%M:%S')}\n" \
               f"Message: {self.message}\n" \
               f"URL: {self.html_url}\n"

def get_commit_history(owner, repo, branch=None, committer=None, since=None, until=None, path=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    commits = []
    page = 1

    while True:
        params = {
            "page": page,
            "per_page": 100,
            "sha": branch,
            "author": committer,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
            "path": path
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            page += 1
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            break

    return commits

def parse_commits(commit_history):
    return [Commit(commit) for commit in commit_history]

def get_commit_details(owner, repo, commit_sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    response = requests.get(url)
    
    if response.status_code == 200:
        commit_data = response.json()
        files = commit_data['files']
        
        changes = []
        for file in files:
            changes.append({
                'filename': file['filename'],
                'status': file['status'],
                'additions': file['additions'],
                'deletions': file['deletions'],
                'changes': file['changes'],
                'patch': file.get('patch', 'No patch available')
            })
        
        return changes
    else:
        print(f"Error fetching commit details: {response.status_code}")
        print(response.text)
        return None