if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo
from bson.objectid import ObjectId
from datetime import datetime
import pymongo

# Para buscar los timestamps limites segun case id para determinar a que case id pertenece 
# el registro que se va a guardar
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


# Se obtiene el ultimo case id asociado a un registro de GitHub
def get_last_case_id_gh(team_project_id):
    team_project = mongo.db.get_collection('registers').find({'team_project_id': ObjectId(team_project_id), 'tool': 'github'}).sort('case_id', pymongo.DESCENDING)
    if(team_project.count() == 0):
        return 0
    case_id = team_project[0]['case_id']
    return case_id

# Se obtiene la informacion de autenticacion desde la fuente de informacion de GitHub
def get_authentication_info(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    token = source['token']
    user = source['user']
    return token, user


# Se obtiene la informacion de la fuente de informacion de GitHub
def get_source_info(team_project_id, source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    team = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_project_id)})
    repo_name = source['name']
    case_id = team['case_id']
    return repo_name, case_id


# Se obtienen los documentos que poseen la informacion del repositorio, de cada commit, 
# para calcular la participaciona a partir de esta
def get_github_info(team_project_id, source_id, date_type):
    github_info = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id, date_type: {'$exists': True}})
    return github_info, last_date_exists


# Se obtiene la ultima fecha de revision segun el tipo de fecha (registros, participacion)
def get_github_info_last_date(team_project_id, source_id, date_type):
    github_info = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_date = github_info[date_type]
    return last_date


# Se guarda un registro asociado a GitHub que sera utilizado en process mining
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


# Se actualiza la ultima fecha de extraccion de registros para process mining
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


# Se obtiene el nombre del repositorio de la fuente de informacion de GitHub
def get_repo_name(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    repo_name = source['name']
    return repo_name


# Se obtiene la participacion de los desarrolladores (cada documento, un desarrollador)
def get_participation(team_project_id, source_id):
    github_part = mongo.db.get_collection('github_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return github_part


# Se actualiza la participacion de un desarrollador
def update_github_participation(team_project_id, source_id, developer, new_additions, new_deletions, new_commits, new_files_added):
    mongo.db.get_collection('github_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'name': developer}, {'$set': {
                'additions': new_additions,
                'deletions': new_deletions,
                'commits': new_commits,
                'files_added': new_files_added
            }})


# Se inserta la participacion de un desarrollador
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


# Se actualiza la informacion de la fuente de informacion: los totales y las fechas de ultimas revisiones
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


# Se actualiza la participacion de un desarrollador
def update_developer_github_participation(team_project_id, source_id, developer, additions_per, deletions_per, commits_per, files_added_per):
    mongo.db.get_collection('github_participation').update_one({'team_project_id': team_project_id, 'source_id': source_id, 'name': developer}, {'$set': {
                'additions_per': additions_per,
                'deletions_per': deletions_per,
                'commits_per': commits_per,
                'files_added_per': files_added_per
            }})


# Para encontrar el documento de participacion asociado a un desarrollador
def find_developer(team_project_id, source_id, developer):
    developer_db = mongo.db.get_collection('github_participation').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'name': developer})
    return developer_db


# Para encontrar a los desarrolladores que han tenido participacion en GitHub
def find_developers(team_project_id, source_id):
    developers = mongo.db.get_collection('github_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return developers


# Para obtener la informacion de la fuente de informacion: totales, fechas
def get_only_github_info(team_project_id, source_id):
    github_info = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    return github_info


# Para obtener los documentos con la participacion de los desarrolladores, cada documento un desarrollador
def get_participation_db(team_project_id, source_id):
    developers = mongo.db.get_collection('github_participation').find({'team_project_id': team_project_id, 'source_id': source_id})
    return developers


# Para saber si existe el atributo total_additions en el documento de github_info de un proyecto
def get_info_total_additions_exists(team_project_id, source_id):
    info_additions_exists = mongo.db.get_collection('github_info').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'total_additions': {'$exists': True}})
    return info_additions_exists


# Para agregar un documento con la informacion de un commit del repositorio, 
# los que se usaran para calcular la participacion de los desarrolladores
def insert_github_repo_info(commit_sha, author, additions, timestamp, team_project_id, source_id):
    mongo.db.get_collection('github_repo_info').insert_one({
        'commit_sha': commit_sha, 
        'author': author, 
        'additions': additions, 
        'timestamp': timestamp,
        'team_project_id': team_project_id,
        'source_id': source_id
    })


# Para obtener los totales de las metricas que se muestran en la participacion
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

# Para obtener los nombres de usuario de los desarrolladores que han participado en el desarrollo
def get_developers(team_project_id):
    developers = mongo.db.get_collection('github_repo_info').find({'team_project_id': team_project_id}).distinct('author')
    return developers

# Para obtener los nombres de usuario de los desarrolladores que han participado en el desarrollo
def get_developers_names(team_project_id, start, end):
    developers = mongo.db.get_collection('github_repo_info').find({'team_project_id': team_project_id, 'timestamp': {'$gte': start, '$lte': end}})
    return developers

# Para obtener los documentos con la informacion de cada commit y poder calcular la productividad
# individual con estos posteriormente
def get_prod_docs_by_developer(team_project_id, developer):
    docs = mongo.db.get_collection('github_repo_info').find({'team_project_id': team_project_id, 'author': developer})
    if docs.count() != 0:
        return docs
    return None


# Para obtener los id de los proyectos asociados a un equipo de desarrollo
def get_projects(team_id):
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    return team['projects']
    