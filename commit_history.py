import requests
from datetime import datetime
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QTextEdit
from PyQt5.QtCore import Qt



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

def print_formatted_commits(commits):
    for commit in commits:
        print(commit)
        print("-" * 50)

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

def print_commit_changes(owner, repo, commit):
    changes = get_commit_details(owner, repo, commit.sha)
    if changes:
        print(f"Changes for commit {commit.sha[:7]}:")
        for change in changes:
            print(f"File: {change['filename']}")
            print(f"Status: {change['status']}")
            print(f"Additions: {change['additions']}, Deletions: {change['deletions']}, Changes: {change['changes']}")
            print("Diff:")
            print(change['patch'])
            print("-" * 50)
    else:
        print(f"No changes found for commit {commit.sha[:7]}")



class CommitHistoryGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Commit History Viewer")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Input fields
        input_layout = QHBoxLayout()
        self.owner_entry = QLineEdit()
        self.repo_entry = QLineEdit()
        self.branch_entry = QLineEdit()
        self.committer_entry = QLineEdit()
        self.since_entry = QLineEdit()
        self.until_entry = QLineEdit()
        self.path_entry = QLineEdit()

        input_layout.addWidget(QLabel("Owner:"))
        input_layout.addWidget(self.owner_entry)
        input_layout.addWidget(QLabel("Repo:"))
        input_layout.addWidget(self.repo_entry)
        input_layout.addWidget(QLabel("Branch:"))
        input_layout.addWidget(self.branch_entry)
        input_layout.addWidget(QLabel("Committer:"))
        input_layout.addWidget(self.committer_entry)

        input_layout2 = QHBoxLayout()
        input_layout2.addWidget(QLabel("Since (YYYY-MM-DD):"))
        input_layout2.addWidget(self.since_entry)
        input_layout2.addWidget(QLabel("Until (YYYY-MM-DD):"))
        input_layout2.addWidget(self.until_entry)
        input_layout2.addWidget(QLabel("Path:"))
        input_layout2.addWidget(self.path_entry)

        fetch_button = QPushButton("Fetch Commits")
        fetch_button.clicked.connect(self.fetch_commits)
        input_layout2.addWidget(fetch_button)

        layout.addLayout(input_layout)
        layout.addLayout(input_layout2)

        # Treeview for commits
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Date", "Author", "Message"])
        self.tree.itemClicked.connect(self.show_commit_details)
        layout.addWidget(self.tree)

        # Commit details text
        self.details_text = QTextEdit()
        layout.addWidget(self.details_text)

    def fetch_commits(self):
        owner = self.owner_entry.text()
        repo = self.repo_entry.text()
        branch = self.branch_entry.text() or None
        committer = self.committer_entry.text() or None
        since = self.parse_date(self.since_entry.text())
        until = self.parse_date(self.until_entry.text())
        path = self.path_entry.text() or None

        try:
            commits = get_commit_history(owner, repo, branch, committer, since, until, path)
            self.display_commits(commits)
        except Exception as e:
            self.details_text.setText(f"Error: {str(e)}")

    def parse_date(self, date_string):
        if date_string:
            try:
                return datetime.strptime(date_string, "%Y-%m-%d")
            except ValueError:
                self.details_text.setText(f"Invalid date format: {date_string}")
        return None

    def display_commits(self, commits):
        self.tree.clear()
        for commit in commits:
            c = Commit(commit)
            item = QTreeWidgetItem(self.tree)
            item.setText(0, c.date.strftime('%Y-%m-%d %H:%M:%S'))
            item.setText(1, c.author_name)
            item.setText(2, c.message)
            item.setData(0, Qt.UserRole, c.sha)

    def show_commit_details(self, item):
        commit_sha = item.data(0, Qt.UserRole)
        owner = self.owner_entry.text()
        repo = self.repo_entry.text()

        changes = get_commit_details(owner, repo, commit_sha)
        if changes:
            details = f"Changes for commit {commit_sha[:7]}:\n\n"
            for change in changes:
                details += f"File: {change['filename']}\n"
                details += f"Status: {change['status']}\n"
                details += f"Additions: {change['additions']}, Deletions: {change['deletions']}, Changes: {change['changes']}\n"
                details += "Diff:\n"
                details += change['patch']
                details += "\n" + "-"*50 + "\n"
        else:
            details = f"No changes found for commit {commit_sha[:7]}"

        self.details_text.setText(details)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CommitHistoryGUI()
    gui.show()
    sys.exit(app.exec_())



    



# owner = "rafeyrana"
# repo = "DAILY-PM"
# branch = "main" 
# committer = "rafeyrana"  
# since = datetime(2024, 1, 1) 
# until = datetime(2024, 12, 31)
# file_name = "README.md" 

# commit_history = get_commit_history(owner, repo, branch=branch, committer=committer, since=since, until=until, path=file_name)
# parsed_commits = parse_commits(commit_history)

# for commit in parsed_commits:
#     print(commit)
#     print_commit_changes(owner, repo, commit)
#     print("=" * 80)