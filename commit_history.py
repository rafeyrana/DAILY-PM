import requests

def get_commit_history(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    commits = []
    page = 1

    while True:
        params = {"page": page, "per_page": 100}
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

# Example usage
owner = "rafeyrana"
repo = "DAILY-PM"
commit_history = get_commit_history(owner, repo)
print(commit_history)