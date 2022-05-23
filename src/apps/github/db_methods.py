if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo
from bson.objectid import ObjectId
from datetime import datetime
import pymongo

def search_timestamps(case_id, ant, team_project_id):
    team_project_min = mongo.db.get_collection('registers').find({'team_project_id': team_project_id, 'case_id': ant}).sort('timestamp', pymongo.DESCENDING)
    team_project_max = mongo.db.get_collection('registers').find({'team_project_id': team_project_id, 'case_id': case_id}).sort('timestamp', pymongo.DESCENDING)
    if(team_project_max.count() > 0):
        max = team_project_max[0]['timestamp']
    else:
        max = 0
    if(team_project_min.count() > 0):
        min = team_project_min[0]['timestamp']
    else:
        min = 0
    return min, max

def get_last_case_id_gh(team_project_id):
    team_project = mongo.db.get_collection('registers').find({'team_project_id': ObjectId(team_project_id), 'tool': 'github'}).sort('case_id', pymongo.DESCENDING)
    if(team_project.count() == 0):
        return 0
    case_id = team_project[0]['case_id']
    return case_id

def get_authentication_info(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    token = source['token']
    user = source['user']
    return token, user

def get_source_info(team_project_id, source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    team = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_project_id)})
    repo_name = source['name']
    case_id = team['case_id']
    return repo_name, case_id

def get_github_info(team_project_id, source_id, date_type):
    github_info = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id, date_type: {'$exists': True}})
    return github_info, last_date_exists

def get_github_info_last_date(team_project_id, source_id, date_type):
    github_info = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_date = github_info[date_type]
    return last_date

def save_register(team_project_id, case_id, activity, time, author):
    mongo.db.get_collection('registers').insert_one({
                            'team_project_id': team_project_id,
                            'case_id': case_id,
                            'activity': activity, 
                            'timestamp': time,
                            'resource': author,
                            'tool': 'github',
                            'userName': author
                            })

def update_last_date(github_info, team_project_id, source_id, repo_name):
    if github_info == None:
        mongo.db.get_collection('github_info').insert_one({
            'team_project_id': team_project_id,
            'source_id': source_id,
            'repo': repo_name, 
            'last_date': datetime.now()
        })
    # Se actualiza el last_date (ultima fecha de revision)
    else:
        mongo.db.get_collection('github_info').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set': {
            'last_date': datetime.now()
        }})

def get_repo_name(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    repo_name = source['name']
    return repo_name

def get_participation(team_project_id, source_id):
    github_part = mongo.db.get_collection('github_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return github_part

def update_github_participation(team_project_id, source_id, developer, new_additions, new_deletions, new_commits, new_files_added):
    mongo.db.get_collection('github_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'name': developer}, {'$set': {
                'additions': new_additions,
                'deletions': new_deletions,
                'commits': new_commits,
                'files_added': new_files_added
            }})

def insert_github_participation(team_project_id, source_id, developer, developers):
    mongo.db.get_collection('github_participation').insert_one({
                'team_project_id': team_project_id, 
                'source_id': source_id,
                'name': developer,
                'additions': developers[developer]['additions'],
                'deletions': developers[developer]['deletions'],
                'commits': developers[developer]['commits'],
                'files_added': developers[developer]['files_added'],
            })

def update_info(github_info, team_project_id, source_id, repo_name, total_additions, total_deletions, total_commits, total_files_added,last_date_commit):
    if github_info == None:
        mongo.db.get_collection('github_info').insert_one({
                'team_project_id': team_project_id,
                'source_id': source_id,
                'repo': repo_name,
                'total_additions': total_additions, 
                'total_deletions': total_deletions,
                'total_commits': total_commits, 
                'total_files_added': total_files_added,
                'last_date_info': datetime.now(), # Indica la fecha en que se reviso por ultima vez
                'last_date_commit': last_date_commit # Indica la fecha del ultimo commit revisado
            })
    else:
        mongo.db.get_collection('github_info').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set': {
                'total_additions': total_additions, 
                'total_deletions': total_deletions,
                'total_commits': total_commits,
                'total_files_added': total_files_added,
                'last_date_info': datetime.now(),
                'last_date_commit': last_date_commit
            }})

def update_developer_github_participation(team_project_id, source_id, developer, additions_per, deletions_per, commits_per, files_added_per):
    mongo.db.get_collection('github_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'name': developer}, {'$set': {
                'additions_per': additions_per,
                'deletions_per': deletions_per,
                'commits_per': commits_per,
                'files_added_per': files_added_per
            }})

def find_developer(team_project_id, source_id, developer):
    developer_db = mongo.db.get_collection('github_participation').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'name': developer})
    return developer_db

def find_developers(team_project_id, source_id):
    developers = mongo.db.get_collection('github_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return developers

def get_only_github_info(team_project_id, source_id):
    github_info = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    return github_info

def translate_name(db_developers, part_name):
    for dev in db_developers:
        if(dev['github'] == part_name):
            return dev['name'], dev
    return None, None

def find_team_developers(team_project_id):
    teams = mongo.db.get_collection('team').find({'projects': {'$exists': True}, 'developers': {'$exists': True}})
    for team in teams:
        projects = team['projects']
        for p in projects:
            if(p == team_project_id):
                return team['developers']
    return None

def get_participation_db_2(team_project_id, source_id):
    developers = mongo.db.get_collection('github_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    developers_db = find_team_developers(team_project_id)
    print(developers_db)
    developers_db_names = []
    if(developers_db != None):
        for dev in developers_db:
            developer = mongo.db.get_collection('developer').find_one({'_id': ObjectId(dev)})
            developers_db_names.append(developer)
    developers_send = []
    for dev in developers:
        name, developer = translate_name(developers_db_names, dev['name'])
        if(name != None):
            developers_db_names.remove(developer)
            dev['name'] = name
        developers_send.append(dev)
    for dev in developers_db_names:
        name = dev['name']
        developers_send.append({
            'name': name, 
            'commits_per': 0,
            'additions_per': 0, 
            'deletions_per': 0,
            'files_added_per': 0
        })
    return developers_send

def get_participation_db(team_project_id, source_id):
    developers = mongo.db.get_collection('github_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return developers

def get_info_total_additions_exists(team_project_id, source_id):
    info_additions_exists = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'total_additions': {'$exists': True}})
    return info_additions_exists

def insert_github_repo_info(commit_sha, author, additions, timestamp, team_project_id, source_id):
    mongo.db.get_collection('github_repo_info').insert_one({
        'commit_sha': commit_sha, 
        'author': author, 
        'additions': additions, 
        'timestamp': timestamp,
        'team_project_id': team_project_id,
        'source_id': source_id
    })

def get_totals(team_project_id, source_id):
    totals = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    totals_send = {}
    if totals != None:
        totals_send['total_additions'] = totals['total_additions']
        totals_send['total_deletions'] = totals['total_deletions']
        totals_send['total_commits'] = totals['total_commits']
        totals_send['total_files_added'] = totals['total_files_added']
    
    return totals_send

#################################################
############### PRODUCTIVITY ####################
#################################################

def get_developers(team_project_id):
    developers = mongo.db.get_collection('github_repo_info').find({'team_project_id': team_project_id}).distinct('author')
    return developers

def get_developers_2(team_id):
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    developers = team['developers']
    return developers

def get_developer_names(dev_id):
    dev = mongo.db.get_collection('developer').find_one({'_id': ObjectId(dev_id)})
    github_name = dev['github']
    name = dev['name']
    return github_name, name

def get_prod_docs(team_project_id):
    docs = mongo.db.get_collection('github_repo_info').find({'team_project_id': team_project_id})
    return docs

def get_prod_docs_by_developer(team_project_id, developer):
    docs = mongo.db.get_collection('github_repo_info').find({'team_project_id': team_project_id, 'author': developer})
    if docs.count() != 0:
        return docs
    return None