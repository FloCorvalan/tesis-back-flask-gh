############################ ACTIVIDADES ############################

EXPRESSIONS = ['code', 'test']

#####################################################################

import json
from github import Github
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import re

import github
from .db_methods import *


def get_authenticated_user(source_id):
    token, user = get_authentication_info(source_id)
    g = Github(token)
    return g.get_user(user)

def is_in_reg_expressions(ex_list, filename):
    for ex in ex_list:
        exp = '^' + ex + '$'
        #print(exp)
        #print(filename)
        res = re.search(exp, filename)
        #print(res)
        if res != None:
            return True
    return False

def extract_reg_expressions():
    filepath = '/home/florencia/tesis-folder/tesis-back-flask-gh/src/apps/github/RegularExpressions.csv'
    file = open(filepath)
    lines = file.readlines()
    expressions = {}
    for line in lines:
        split_line = line.strip('\n').split(',')
        name = split_line[0]
        row = split_line[1:]
        expressions[name] = row
        row = []
        name = ''
    #print(expressions)
    return expressions

def get_registers(team_id, source_id):

    dic = extract_reg_expressions()

    repo_name, case_id = get_source_info(team_id, source_id)

    user = get_authenticated_user(source_id)

    repo = user.get_repo(repo_name)
    branches = repo.get_branches()

    github_info, last_date_exists = get_github_info(team_id, source_id, 'last_date')
   
    commits_sha = []
    for branch in branches:
        if github_info == None or last_date_exists == None:
            #### Se analizan todos los datos existentes
            commits = repo.get_commits(branch.name)
        else:
            # Si se han analizado datos ya
            # Se analizan los datos posteriores a la ultima
            #fecha de revision
            last_date = get_github_info_last_date(team_id, source_id, 'last_date')
            commits = repo.get_commits(branch.name, since=last_date)
        print("RAMA " + branch.name)
        for commit in commits:
            if commit.sha not in commits_sha:
                commits_sha.append(commit.sha)
                #print(commit)
                # Se deben analizar los nombres de los archivos que fueron modificados
                author = commit.commit.author.name
                time = commit.commit.author.date
                i = 0
                min_changes = 0 # esto deberia ser un numero mayor pero no se cual aun
                number_changes = {}
                for ex in EXPRESSIONS:
                    number_changes[ex] = 0
                activity = ''
                while i < len(commit.files):
                    for ex in EXPRESSIONS:
                        if is_in_reg_expressions(dic[ex], commit.files[i].filename) and commit.files[i].changes > min_changes: 
                            number_changes[ex] += commit.files[i].changes
                            #print('commit.files[i].changes')
                            #print(commit.files[i].changes)
                    i += 1
                max_changes = 0
                for ex in EXPRESSIONS:
                    if number_changes[ex] > max_changes:
                        activity = 'IMPLEMENTACION_' + ex
                        max_changes = number_changes[ex]
                #print(max_changes)
                if activity != '':
                    print('REGISTER')
                    print({
                            'team_id': team_id,
                            'case_id': case_id,
                            'activity': activity, 
                            'timestamp': time,
                            'resource': author,
                            'tool': 'github',
                            'userName': author
                            })
                    time = datetime.strptime(str(time).split(".")[0], "%Y-%m-%d %H:%M:%S").timestamp()
                    save_register(team_id, case_id, activity, time, author)
    print(github_info)
    update_last_date(github_info, team_id, source_id, repo_name) # Si no existe, la crea

    return {'message': 'Successfully extracted data'}


#################################################
############# PARTICIPATION #####################
#################################################
def get_repo_info(team_id, source_id):
    repo_name = get_repo_name(source_id)

    user = get_authenticated_user(source_id)

    repo = user.get_repo(repo_name)
    branches = repo.get_branches()

    github_info, last_date_exists = get_github_info(team_id, source_id, 'last_date_info')

    developers = {}

    # Se obtiene en numero total de commits
    commits_sha = []
    for branch in branches:
        if github_info == None or last_date_exists == None:
            #print('entre al IF')
            commits = repo.get_commits(branch.name)
        else:
            #print('entre al ELSE')
            last_date = get_github_info_last_date(team_id, source_id, 'last_date_info')
            commits = repo.get_commits(branch.name, since=last_date)
            github_part = get_participation(team_id, source_id)
            for developer in github_part:
                developers[developer['name']] = {
                    'additions': developer['additions'],
                    'deletions': developer['deletions'],
                    'commits': developer['commits']
                }
        #print("RAMA " + branch.name)
        #cont = 0
        for commit in commits:
            print(commit.commit.author.date)
            if commit.sha not in commits_sha:
                commits_sha.append(commit.sha)
                author = commit.commit.author.name
                if author not in developers.keys():
                    developers[author] = {
                        'additions': 0,
                        'deletions': 0,
                        'commits': 1
                    }
                else:
                    developers[author]['commits'] += 1
                additions = 0
                deletions = 0
                #print('Contador = ' + str(cont))
                for file in commit.files:
                    additions += file.additions
                    deletions += file.deletions
                    #print(file.additions)
                    #print(file.deletions)
                developers[author]['additions'] += additions
                developers[author]['deletions'] += deletions
                
                #cont += 1
        '''print('ADDITIONS DEVELOPER TOTAL')
        print(developers[author]['additions'])
        print('DELETIONS DEVELOPER TOTAL')
        print(developers[author]['deletions'])
        print('COMMITS DEVELOPER TOTAL')
        print(developers[author]['commits'])'''

    # Se calculan los totales (additions, deletions, commits) en el repositorio
    # primero se revisa si existe la instancia de github info y los atributos necesarios
    # (se asume que si existe uno de los totales es porque ya paso por eso al menos una vez)
    github_additions_exists = get_info_additions_exists(team_id, source_id)
    if github_info == None or github_additions_exists == None:
        # No hay registro previo => los totales actuales son 0
        total_additions = 0
        total_deletions = 0
        total_commits = 0
    else:
        # Si hay registro previo => se obtienen los totales previamente registrados
        total_additions = github_info['total_additions']
        total_deletions = github_info['total_deletions']
        total_commits = github_info['total_commits']

    for developer in developers.keys():
        # Se acumulan los nuevos resultados (de lo que se obtuvo revisando la actividad de los developers)
        total_additions += developers[developer]['additions']
        total_deletions += developers[developer]['deletions']
        total_commits += developers[developer]['commits']
        # Se actualiza la informacion de los developers en github_participation
        developer_db = find_developer(team_id, source_id, developer)
        if developer_db != None:
            # Si existe, se actualizan sus datos
            new_additions = developer_db['additions']
            new_deletions = developer_db['deletions']
            new_commits = developer_db['commits']
            update_github_participation(team_id, source_id, developer, new_additions, new_deletions, new_commits)
        else:
            # Si no existe, se inserta
            #print("se inserta developer en participacion")
            insert_github_participation(team_id, source_id, developer, developers)
    # Se almacenan los totales en github_info
    #print("se actualiza la informacion")
    update_info(github_info, team_id, source_id, repo_name, total_additions, total_deletions, total_commits)

    return developers

def calculate_percentages(team_id, source_id):
    print("entre a calculate_percentages")
    developers = find_developers(team_id, source_id)
    github_info = get_only_github_info(team_id, source_id)
    
    total_additions = github_info['total_additions']
    total_deletions = github_info['total_deletions']
    total_commits = github_info['total_commits']
    for developer in developers:
        additions_per = int(developer['additions']/total_additions * 100)
        deletions_per = int(developer['deletions']/total_deletions * 100)
        commits_per = int(developer['commits']/total_commits * 100)

        update_developer_github_participation(team_id, source_id, developer['name'], additions_per, deletions_per, commits_per)
    return 

def get_participation(team_id, source_id):
    participation = get_participation_db(team_id, source_id)
    return participation