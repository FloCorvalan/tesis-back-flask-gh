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

@github.route('/github-test-2', methods=['GET'])
def test2():
    response = json.dumps(extract_reg_expressions())
    return Response(response, 'application/json')


@github.route('/github-test-3', methods=['GET'])
def test3():
    user = get_authenticated_user("6255d136c04ac27bbad0276d")
    repo = user.get_repo("tesis")
    print(repo)
    branches = repo.get_branches()
    commits_sha = []
    for branch in branches:
        commits = repo.get_commits(branch.name)
        print("RAMA " + branch.name)
        for commit in commits:
            if commit.sha not in commits_sha:
                commits_sha.append(commit.sha)
                print(commit.commit.author.name)


    #return Response(response, 'application/json')

@github.route('/github/get-registers', methods=['GET'])
def get_github_registers():
    response = get_registers('6241fad36d714f635bafbc9f', '6255d136c04ac27bbad0276d')
    return Response(response, 'application/json')
    '''txt = "The rain in Spain"
    x = re.search("^The.*Spain$", txt)
    print(x)'''