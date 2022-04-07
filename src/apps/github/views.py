from fileinput import filename
from sre_constants import BRANCH
from traceback import print_tb
from flask import Blueprint, Response
from .methods import *
import json

github = Blueprint('github', __name__)

@github.route('/github-test', methods=['GET'])
def test():
    user = get_authenticated_user("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")
    repo = user.get_repo("tesis")
    print(repo)
    commits = repo.get_commits()
    for commit in commits:
        print(commit.commit.message)
        print(commit.commit.author.name)
        for file in commit.files:
            print(file.filename)
        code_list = ['.jar', '.py', '.java', '.php', '.vue', '.js', '.r', '.jsx', '.ts', '.go']
        for end in code_list:
            if file in commit.files:
                file.filename.endswith(end)
                print("FUNCIONA")
                return 1
    response = json.dumps(commits)
    return Response(response, 'application/json')