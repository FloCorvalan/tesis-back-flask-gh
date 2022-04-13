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
        print(exp)
        res = re.search(exp, filename)
        print(res)
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
    #github_info = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id})
    repo_name = source['name']
    case_id = team['actual_case_id']
    user = get_authenticated_user(source_id)

    repo = user.get_repo(repo_name)
    branches = repo.get_branches()

    github_info = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id, 'last_date': {'$exists': True}})
    if github_info == None or last_date_exists == None:
        #### Se analizan todos los datos existentes
        commits_sha = []
        for branch in branches:
            commits = repo.get_commits(branch.name)
            print("RAMA " + branch.name)
            for commit in commits:
                if commit.sha not in commits_sha:
                    commits_sha.append(commit.sha)
                    print(commit)
                    # Se deben analizar los nombres de los archivos que fueron modificados
                    author = commit.commit.author.name
                    time = commit.commit.author.date
                    i = 0
                    activity = ''
                    while i < len(commit.files):
                        for ex in EXPRESSIONS:
                            if is_in_reg_expressions(dic[ex], commit.files[i].filename):
                                activity = 'IMPLEMENTACION_' + ex
                                i = len(commit.files)
                        i += 1
                    
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
    else:
        # Si se han analizado datos ya
        # Se analizan los datos posteriores a la ultima
        #fecha de revision
        print("hola")

    
    '''
    if github_info == None:
        mongo.db.get_collection('github_info').insert_one({
            'team_id': team_id,
            'project': repo_name, 
            'last_date': datetime.now(),
            'source_id': source_id
        })
    # Se actualiza el last_date (ultima fecha de revision)
    else:
        mongo.db.get_collection('github_info').update_one({'team_id': team_id, 'source_id': source_id}, {'$set': {
            'last_date': datetime.now()
        }})
    '''
    return {'message': 'Successfully extracted data'}