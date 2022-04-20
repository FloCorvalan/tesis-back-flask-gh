from fileinput import filename
from sre_constants import BRANCH
from traceback import print_tb
from flask import Blueprint, Response
from .methods import *
import json
from bson import json_util

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
    stats_contributors = repo.get_stats_contributors()
    for stat in stats_contributors:
        print(stat.total)
        print('weeks')
        for week in stat.weeks:
            print(week.c)
    #return Response(response, 'application/json')

###################################################################
########################## REGISTERS ##############################
###################################################################

@github.route('/github', methods=['GET'])
def get_registers_service():
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6255d136c04ac27bbad0276d'
    response = get_registers(team_project_id, source_id)
    return response

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------

@github.route('/github/get-repo-info', methods=['GET'])
def get_github_repo_info():
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6255d136c04ac27bbad0276d'
    response = get_repo_info(team_project_id, source_id)
    return response

###################################################################
################### ALL PARTICIPATION PROCESS #####################
###################################################################

@github.route('/github/participation', methods=['GET'])
def get_github_participation():
    #team_project_id = request.json['team_project_id']
    #source_id = request.json['source_id']
    team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = '6255d136c04ac27bbad0276d'
    # Se obtiene la informacion general del repositorio (totales) y de los desarrolladores
    get_repo_info(team_project_id, source_id)

    # Se calculan los porcentajes de participacion de los desarrolladores
    calculate_percentages(team_project_id, source_id)

    # Se obtiene la participacion de los desarrolladores
    participation = get_participation(team_project_id, source_id)
    
    response = json_util.dumps(participation)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------