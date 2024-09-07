import sys
import openai
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter
from PyQt5.QtCore import Qt
from dotenv import load_dotenv
import os
from utils.commit_utils import get_commit_history, parse_commits, get_commit_details, Commit
import json
from PyQt5.QtWidgets import QMessageBox

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class VirtualPMGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Virtual Project Manager")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side: Chat interface
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        chat_layout.addWidget(self.chat_history)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.send_button)

        # Right side: Parameter inputs and commit display
        param_commit_widget = QWidget()
        param_commit_layout = QVBoxLayout(param_commit_widget)

        # Parameter inputs
        param_layout = QHBoxLayout()
        self.owner_entry = QLineEdit()
        self.repo_entry = QLineEdit()
        self.branch_entry = QLineEdit()
        self.committer_entry = QLineEdit()
        self.since_entry = QLineEdit()
        self.until_entry = QLineEdit()
        self.path_entry = QLineEdit()

        param_layout.addWidget(QLabel("Owner:"))
        param_layout.addWidget(self.owner_entry)
        param_layout.addWidget(QLabel("Repo:"))
        param_layout.addWidget(self.repo_entry)
        param_layout.addWidget(QLabel("Branch:"))
        param_layout.addWidget(self.branch_entry)
        param_layout.addWidget(QLabel("Committer:"))
        param_layout.addWidget(self.committer_entry)

        param_layout2 = QHBoxLayout()
        param_layout2.addWidget(QLabel("Since:"))
        param_layout2.addWidget(self.since_entry)
        param_layout2.addWidget(QLabel("Until:"))
        param_layout2.addWidget(self.until_entry)
        param_layout2.addWidget(QLabel("Path:"))
        param_layout2.addWidget(self.path_entry)

        fetch_button = QPushButton("Fetch Commits")
        fetch_button.clicked.connect(self.fetch_commits_from_params)
        param_layout2.addWidget(fetch_button)

        param_commit_layout.addLayout(param_layout)
        param_commit_layout.addLayout(param_layout2)

        # Commit display
        self.commit_tree = QTreeWidget()
        self.commit_tree.setHeaderLabels(["Date", "Author", "Message"])
        self.commit_tree.itemClicked.connect(self.show_commit_details)
        
        self.commit_details = QTextEdit()
        self.commit_details.setReadOnly(True)

        commit_splitter = QSplitter(Qt.Vertical)
        commit_splitter.addWidget(self.commit_tree)
        commit_splitter.addWidget(self.commit_details)

        param_commit_layout.addWidget(commit_splitter)

        # summary button
        self.summary_button = QPushButton("Generate Summary")
        self.summary_button.clicked.connect(self.generate_summary)
        param_commit_layout.addWidget(self.summary_button)
        # Add widgets to main layout
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(chat_widget)
        main_splitter.addWidget(param_commit_widget)
        main_layout.addWidget(main_splitter)

    def send_message(self):
        query = self.chat_input.text()
        self.chat_history.append(f"You: {query}")
        self.chat_input.clear()

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a virtual project manager assistant. Your task is to extract information from user queries about GitHub commit history. Extract the following information if present: owner, repo, branch, committer, since date, until date, and file path. Format the output as a Python dictionary."},
                {"role": "user", "content": query}
            ]
        )

        parsed_info = eval(response.choices[0].message['content'])
        self.chat_history.append(f"Assistant: I've parsed the following information:\n{parsed_info}")

        self.owner_entry.setText(parsed_info.get('owner', ''))
        self.repo_entry.setText(parsed_info.get('repo', ''))
        self.branch_entry.setText(parsed_info.get('branch', ''))
        self.committer_entry.setText(parsed_info.get('committer', ''))
        self.since_entry.setText(parsed_info.get('since', ''))
        self.until_entry.setText(parsed_info.get('until', ''))
        self.path_entry.setText(parsed_info.get('path', ''))

        self.fetch_commits_from_params()

    def fetch_commits_from_params(self):
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
            self.commit_details.setText(f"Error: {str(e)}")



    def generate_summary(self):
        commits = self.get_displayed_commits()
        diffs = self.get_commit_diffs()

        if not commits:
            QMessageBox.warning(self, "No Commits", "No commits have been fetched. Please fetch commits first.")
            return

        prompt = self.create_summary_prompt(commits, diffs)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo", 
                messages=[
                    {"role": "system", "content": "You are a project manager assistant. Your task is to provide a detailed summary of the contributions and progress based on the commit history and code changes."},
                    {"role": "user", "content": prompt}
                ]
            )

            summary = response.choices[0].message['content']
            self.display_summary(summary)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while generating the summary: {str(e)}")

    def get_displayed_commits(self):
        commits = []
        for i in range(self.commit_tree.topLevelItemCount()):
            item = self.commit_tree.topLevelItem(i)
            commit = {
                "date": item.text(0),
                "author": item.text(1),
                "message": item.text(2),
                "sha": item.data(0, Qt.UserRole)
            }
            commits.append(commit)
        return commits

    def get_commit_diffs(self):
        diffs = {}
        for i in range(self.commit_tree.topLevelItemCount()):
            item = self.commit_tree.topLevelItem(i)
            sha = item.data(0, Qt.UserRole)
            owner = self.owner_entry.text()
            repo = self.repo_entry.text()
            changes = get_commit_details(owner, repo, sha)
            if changes:
                diffs[sha] = changes
        return diffs

    def create_summary_prompt(self, commits, diffs):
        prompt = "Please provide a detailed summary of the following commits and code changes:\n\n"
        prompt += "Commits:\n"
        for commit in commits:
            prompt += f"- {commit['date']} by {commit['author']}: {commit['message']} (SHA: {commit['sha']})\n"

        prompt += "\nCode Changes:\n"
        for sha, changes in diffs.items():
            prompt += f"Commit {sha[:7]}:\n"
            for change in changes:
                prompt += f"  File: {change['filename']}\n"
                prompt += f"  Status: {change['status']}\n"
                prompt += f"  Additions: {change['additions']}, Deletions: {change['deletions']}, Changes: {change['changes']}\n"
                prompt += f"  Diff:\n{change['patch']}\n\n"

        prompt += "\nBased on these commits and code changes, please provide:\n"
        prompt += "1. An overview of the main contributions and progress made\n"
        prompt += "2. Key features or improvements implemented\n"
        prompt += "3. Any notable code refactoring or architectural changes\n"
        prompt += "4. Potential areas of concern or technical debt introduced\n"
        prompt += "5. Suggestions for next steps or areas that might need attention\n"

        return prompt

    def display_summary(self, summary):
        summary_dialog = QMessageBox(self)
        summary_dialog.setWindowTitle("Contribution Summary")
        summary_dialog.setText(summary)
        summary_dialog.setDetailedText(summary)
        summary_dialog.setStandardButtons(QMessageBox.Ok)
        summary_dialog.exec_()


    def parse_date(self, date_string):
        if date_string:
            try:
                return datetime.strptime(date_string, "%Y-%m-%d")
            except ValueError:
                self.commit_details.setText(f"Invalid date format: {date_string}")
        return None

    def display_commits(self, commits):
        self.commit_tree.clear()
        for commit in commits:
            c = Commit(commit)
            item = QTreeWidgetItem(self.commit_tree)
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

        self.commit_details.setText(details)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = VirtualPMGUI()
    gui.show()
    sys.exit(app.exec_())