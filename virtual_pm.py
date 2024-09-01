import openai
from datetime import datetime, timedelta
from commit_history import get_commit_history, parse_commits

import os
from dotenv import load_dotenv


load_dotenv()


openai.api_key = os.getenv("OPENAI_API_KEY")

def virtual_project_manager(query):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a virtual project manager assistant. Your task is to extract information from user queries about GitHub commit history. Extract the following information if present: owner, repo, branch, committer, since date, until date, and file path. Format the output as a Python dictionary."},
            {"role": "user", "content": query}
        ]
    )

    parsed_info = eval(response.choices[0].message['content'])
    print(f"this is is the parsed info: %s" % parsed_info)
    owner = parsed_info.get('owner', '')
    repo = parsed_info.get('repo', '')
    branch = parsed_info.get('branch')
    committer = parsed_info.get('committer')
    since = datetime.strptime(parsed_info['since'], "%Y-%m-%d") if 'since' in parsed_info else None
    until = datetime.strptime(parsed_info['until'], "%Y-%m-%d") if 'until' in parsed_info else None
    path = parsed_info.get('path')

    commits = get_commit_history(owner, repo, branch, committer, since, until, path)
    parsed_commits = parse_commits(commits)

    # Print the results
    print(f"Commit history for {owner}/{repo}:")
    print("-" * 50)
    for commit in parsed_commits:
        print(commit)
        print("-" * 50)

if __name__ == "__main__":
    query = input("Enter your query about GitHub commit history: ")
    virtual_project_manager(query)