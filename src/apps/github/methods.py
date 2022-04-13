############################ ACTIVIDADES ############################

EXPRESSIONS = ['code', 'test']

#####################################################################


if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo

import json
from github import Github
from bson.objectid import ObjectId
from datetime import datetime
import re


def get_authenticated_user(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    token = source['token']
    user = source['user']
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

    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    repo_name = source['name']
    case_id = team['actual_case_id']
    user = get_authenticated_user(source_id)

    repo = user.get_repo(repo_name)
    branches = repo.get_branches()

    github_info = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id, 'last_date': {'$exists': True}})
        
    commits_sha = []
    for branch in branches:
        if github_info == None or last_date_exists == None:
            #### Se analizan todos los datos existentes
            commits = repo.get_commits(branch.name)
        else:
            # Si se han analizado datos ya
            # Se analizan los datos posteriores a la ultima
            #fecha de revision
            last_date = github_info['last_date']
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
                    '''
                    mongo.db.get_collection('registers').insert_one({
                            'team_id': team_id,
                            'case_id': case_id,
                            'activity': activity, 
                            'timestamp': time,
                            'resource': author,
                            'tool': 'github',
                            'userName': author
                            })

                    ''' 
    '''
    if github_info == None:
        mongo.db.get_collection('github_info').insert_one({
            'team_id': team_id,
            'source_id': source_id,
            'repo': repo_name, 
            'last_date': datetime.now()
        })
    # Se actualiza el last_date (ultima fecha de revision)
    else:
        mongo.db.get_collection('github_info').update_one({'team_id': team_id, 'source_id': source_id}, {'$set': {
            'last_date': datetime.now()
        }})
    '''
    return {'message': 'Successfully extracted data'}


#################################################
############# PARTICIPACION #####################
#################################################
def get_repo_info(team_id, source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    repo_name = source['name']
    user = get_authenticated_user(source_id)

    repo = user.get_repo(repo_name)
    branches = repo.get_branches()

    github_info = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id, 'last_date_info': {'$exists': True}})

    developers = {}

    # Se obtiene en numero total de commits
    commits_sha = []
    for branch in branches:
        if github_info == None or last_date_exists == None:
            commits = repo.get_commits(branch.name)
        else:
            last_date = github_info['last_date_info']
            commits = repo.get_commits(branch.name, since=last_date)
            github_part = mongo.db.get_collection('github_participation').find({'team_id': team_id, 'source_id': source_id})
            for developer in github_part:
                developers[developer['name']] = {
                    'additions': developer['additions'],
                    'deletions': developer['deletions'],
                    'commits': developer['commits']
                }
        #print("RAMA " + branch.name)
        for commit in commits:
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
                for file in commit.files:
                    additions += file.additions
                    deletions += file.deletions
                developers[author]['additions'] += additions
                developers[author]['deletions'] += deletions

    # Se calculan los totales (additions, deletions, commits) en el repositorio
    if github_info == None:
        # No hay registro previo => los totales actuales son 0
        total_additions = 0
        total_deletions = 0
        total_commits = 0
    else:
        # Si hay registro previo => se obtienen los totales previamente registrados
        total_additions = github_info['total_additions']
        total_deletions = github_info['total_deletions']
        total_commits = github_info['total_commits']

    '''new_total_additions = 0
    new_total_deletions = 0
    new_total_commits = 0'''
    for developer in developers.keys():
        # Se acumulan los nuevos resultados (de lo que se obtuvo revisando la actividad de los developers)
        total_additions += developers[developer]['additions']
        total_deletions += developers[developer]['deletions']
        total_commits += developers[developer]['commits']
        # Se actualiza la informacion de los developers en github_participation
        developer_db = mongo.db.get_collection('github_participation').find_one({'team_id': team_id, 'source_id': source_id, 'name': developer})
        if developer_db != None:
            # Si existe, se actualizan sus datos
            new_additions = developer_db['additions'] + developers[developer]['additions']
            new_deletions = developer_db['deletions'] + developers[developer]['deletions']
            new_commits = developer_db['commits'] + developers[developer]['commits']
            mongo.db.get_collection('github_participation').update_one({'team_id': team_id, 'source_id': source_id, 'name': developer}, {'$set': {
                'addtions': new_additions,
                'deletions': new_deletions,
                'commits': new_commits
            }})
        else:
            # Si no existe, se inserta
            mongo.db.get_collection('github_participation').insert_one({
                'team_id': team_id, 
                'source_id': source_id,
                'name': developer,
                'additions': developers[developer]['additions'],
                'deletions': developers[developer]['deletions'],
                'commits': developers[developer]['commits']
            })
    # Se almacenan los totales en github_info
    if github_info == None:
        mongo.db.get_collection('github_info').insert_one({
                'team_id': team_id,
                'source_id': source_id,
                'repo': repo_name,
                'total_additions': total_additions, 
                'total_deletions': total_deletions,
                'total_commits': total_commits, 
                'last_date_info': datetime.now()
            })
    else:
        mongo.db.get_collection('github_info').update_one({'team_id': team_id, 'source_id': source_id}, {'$set': {
                'total_additions': total_additions, 
                'total_deletions': total_deletions,
                'total_commits': total_commits, 
                'last_date_info': datetime.now()
            }})

    return developers