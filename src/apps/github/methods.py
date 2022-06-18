import json
from github import Github
from datetime import datetime, timedelta
import re
from bson import json_util
import pandas as pd
import requests
import os
from .db_methods import *

############################ ACTIVIDADES ############################

EXPRESSIONS = ['code', 'test']

#####################################################################

# Para obtener un usuario autenticado con su token y nombre de usuario en GitHub
def get_authenticated_user(source_id):
    token, user = get_authentication_info(source_id)
    g = Github(token)
    return g.get_user(user)


# Define si un nombre de archivo esta en las regular expressions
def is_in_reg_expressions(ex_list, filename):
    for ex in ex_list:
        exp = '^' + ex + '$'
        res = re.search(exp, filename)
        if res != None:
            return True
    return False


# Extrae las regular expressions desde el archivo RegularExpressions.csv
def extract_reg_expressions():
    pwd = os.getcwd()
    filepath = pwd + '/src/apps/github/RegularExpressions.csv'
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
    return expressions


# Obtiene el case id actual, el que se debe asociar al registro que se va a guardar
def get_actual_case_id(team_project_id, last_case_id, timestamp):
    last_case_id_gh = get_last_case_id_gh(team_project_id)
    cont = last_case_id_gh
    case_id = None
    while(cont < last_case_id):
        ant = cont - 1
        ini, fin = search_timestamps(cont, ant, team_project_id)
        if(timestamp > ini and timestamp <= fin):
            case_id = cont
            return case_id
        cont += 1
    ini, fin = search_timestamps(last_case_id, last_case_id - 1, team_project_id)
    if(timestamp > ini):
        return last_case_id
    return 0


# Genera los registros asociados a GitHub que seran utilizados en process mining
def get_registers(team_project_id, source_id):

    dic = extract_reg_expressions()

    repo_name, last_case_id = get_source_info(team_project_id, source_id)
    user = get_authenticated_user(source_id)

    repo = user.get_repo(repo_name)
    branches = repo.get_branches()

    github_info, last_date_exists = get_github_info(team_project_id, source_id, 'last_date')

    commits_sha = []
    for branch in branches:
        if github_info == None or last_date_exists == None:
            #### Se analizan todos los datos existentes
            commits = repo.get_commits(branch.name)
        else:
            # Si se han analizado datos ya
            # Se analizan los datos posteriores a la ultima
            #fecha de revision
            last_date = get_github_info_last_date(team_project_id, source_id, 'last_date')
            commits = repo.get_commits(branch.name, since=last_date + timedelta(hours=4))
        for commit in commits:
            if commit.sha not in commits_sha:
                commits_sha.append(commit.sha)
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
                    i += 1
                max_changes = 0
                time = datetime.strptime(str(time).split(".")[0], "%Y-%m-%d %H:%M:%S").timestamp() - 14400 #Se restan las 4 horas de diferencia de UTC, la hora de los servidores de GitHub
                case_id = get_actual_case_id(team_project_id, last_case_id, time)
                for ex in EXPRESSIONS:
                    if number_changes[ex] > max_changes:
                        activity = 'IMPLEMENTACION_' + ex
                        save_register(team_project_id, case_id, activity, time, author)
    update_last_date(github_info, team_project_id, source_id, repo_name) # Si no existe, la crea

    return {'message': 'Successfully extracted data'}


#################################################
############# PARTICIPATION #####################
#################################################

# Obtiene la informacion del repositorio, de cada commit, para obtener la participacion de los
# desarrolladores
def get_repo_info(team_project_id, source_id):
    repo_name = get_repo_name(source_id)

    user = get_authenticated_user(source_id)

    repo = user.get_repo(repo_name)
    branches = repo.get_branches()

    github_info, last_date_exists = get_github_info(team_project_id, source_id, 'last_date_commit')

    developers = {}

    total_additions = 0
    total_deletions = 0
    total_commits = 0
    total_files_added = 0

    # Se obtiene en numero total de commits
    commits_sha = []
    last_date = None
    another_branch = 0 # indica si se esta pasando por otra rama para no reiniciar los contadores de developers con lo de la bd
    for branch in branches:
        if github_info == None or last_date_exists == None:
            commits = repo.get_commits(branch.name)
            # Si es None, no se ha pasado por otra rama
            if last_date == None:
                last_date = commits[0].commit.author.date
            # Si no es None, se comprueba que la primera fecha de la siguiente rama
            # sea mayor que la ultima almacenada para guardarla
            elif last_date < commits[0].commit.author.date:
                last_date = commits[0].commit.author.date
        else:
            last_date_db = get_github_info_last_date(team_project_id, source_id, 'last_date_commit')
            if last_date == None:
                last_date = last_date_db
            elif last_date < last_date_db:
                last_date = last_date_db
            commits = repo.get_commits(branch.name, since=last_date + timedelta(seconds=1))
            github_part = get_participation(team_project_id, source_id)
            if another_branch == 0:
                for developer in github_part:
                    developers[developer['name']] = {
                        'additions': developer['additions'],
                        'deletions': developer['deletions'],
                        'commits': developer['commits'],
                        'files_added': developer['files_added']
                    }
        for commit in commits:
            if commit.sha not in commits_sha:
                commits_sha.append(commit.sha)
                author = commit.commit.author.name
                if author not in developers.keys():
                    developers[author] = {
                        'additions': 0,
                        'deletions': 0,
                        'commits': 1,
                        'files_added': 0
                    }
                else:
                    developers[author]['commits'] += 1
                    # Si hay al menos un commit, se debe mantener la cuenta
                    another_branch = 1
                # Se suma uno al total de commits nuevos
                total_commits += 1
                additions = 0
                deletions = 0
                files_added = 0
                for file in commit.files:
                    additions += file.additions
                    deletions += file.deletions
                    
                    # Se suman las additions y deletions totales de los nuevos commits
                    total_additions += file.additions
                    total_deletions += file.deletions

                    if file.status == 'added':
                        files_added += 1
                        total_files_added += 1

                developers[author]['additions'] += additions
                developers[author]['deletions'] += deletions
                developers[author]['files_added'] += files_added
                
                # Se actualiza la fecha con la del commit analizado
                # para finalmente obtener la mayor fecha
                if last_date < commit.commit.author.date:
                    last_date = commit.commit.author.date
                
                # Se guarda la informacion para conocer la productividad
                # en github_repo_info
                time = datetime.strptime(str(commit.commit.author.date).split(".")[0], "%Y-%m-%d %H:%M:%S").timestamp() - 14400
                insert_github_repo_info(commit.commit.sha, author, additions, time, team_project_id, source_id)

    # Se calculan los totales (additions, deletions, commits) en el repositorio
    # primero se revisa si existe la instancia de github info y los atributos necesarios
    # (se asume que si existe uno de los totales es porque ya paso por eso al menos una vez)
    github_additions_exists = get_info_total_additions_exists(team_project_id, source_id)
    if github_info == None or github_additions_exists == None:
        # No hay registro previo => los totales actuales son 0
        new_total_additions = 0
        new_total_deletions = 0
        new_total_commits = 0
        new_total_files_added = 0
    else:
        # Si hay registro previo => se obtienen los totales previamente registrados
        new_total_additions = github_info['total_additions']
        new_total_deletions = github_info['total_deletions']
        new_total_commits = github_info['total_commits']
        new_total_files_added = github_info['total_files_added']
    # Se acumulan los nuevos resultados (de lo que se obtuvo revisando la actividad de los developers)
    new_total_additions += total_additions
    new_total_deletions += total_deletions
    new_total_commits += total_commits
    new_total_files_added += total_files_added

    for developer in developers.keys():
        # Se actualiza la informacion de los developers en github_participation
        developer_db = find_developer(team_project_id, source_id, developer)
        if developer_db != None:
            # Si existe, se actualizan sus datos
            new_additions = developers[developer]['additions']
            new_deletions = developers[developer]['deletions']
            new_commits = developers[developer]['commits']
            new_files_added = developers[developer]['files_added']
            update_github_participation(team_project_id, source_id, developer, new_additions, new_deletions, new_commits, new_files_added)
        else:
            # Si no existe, se inserta
            insert_github_participation(team_project_id, source_id, developer, developers)
    # Se almacenan los totales en github_info
    update_info(github_info, team_project_id, source_id, repo_name, new_total_additions, new_total_deletions, new_total_commits, new_total_files_added, last_date)

    return developers


# Calcula los porcentajes de participacion segun la informacion del repositorio extraida previamente
def calculate_percentages(team_project_id, source_id):
    developers = find_developers(team_project_id, source_id)
    github_info = get_only_github_info(team_project_id, source_id)
    
    total_additions = github_info['total_additions']
    total_deletions = github_info['total_deletions']
    total_commits = github_info['total_commits']
    total_files_added = github_info['total_files_added']
    for developer in developers:
        if total_additions == 0:
            additions_per = 0
        else:
            additions_per = int(developer['additions']/total_additions * 100)
        if total_deletions == 0:
            deletions_per = 0
        else:
            deletions_per = int(developer['deletions']/total_deletions * 100)
        if total_commits == 0:
            commits_per = 0
        else:
            commits_per = int(developer['commits']/total_commits * 100)
        if total_files_added == 0:
            files_added_per = 0
        else:
            files_added_per = int(developer['files_added']/total_files_added * 100)

        update_developer_github_participation(team_project_id, source_id, developer['name'], additions_per, deletions_per, commits_per, files_added_per)
    return 


# Obtiene la participacion de los desarrolladores en GitHub
def get_participation_method(team_project_id, source_id):
    participation = get_participation_db(team_project_id, source_id)
    totals = get_totals(team_project_id, source_id)
    participation_send = {
        'developers': participation,
        'totals': totals
    }
    return participation_send



#################################################
############### PRODUCTIVITY ####################
#################################################

# Obtiene la informacion de la productividad individual de los desarrolladores
def get_prod_info(team_project_id, min_date, max_date):
    developers = get_developers(team_project_id)

    developers_info = []

    for developer in developers:
        docs = get_prod_docs_by_developer(team_project_id, developer)
        if docs != None:
            df = pd.DataFrame(list(docs))
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

            # Se agrega la fecha minima entre las 3 herramientas para hacer los intervalos desde ahi
            min_date_dic = {'timestamp':min_date}
            df = df.append(min_date_dic, ignore_index=True)

            # Se agrega la fecha máxima entre las 3 herramientas para hacer los intervalos hasta ahi
            max_date_dic = {'timestamp':max_date}
            df = df.append(max_date_dic, ignore_index=True)

            # Se crea un dataframe para las additions en intervalos
            df1 = df.resample('D', on='timestamp')['additions'].sum()
            df1 = pd.DataFrame(df1)

            # Se crea un dataframe para los commits en intervalos
            df2 = df.resample('D', on='timestamp')['additions'].count()
            df2 = pd.DataFrame(df2)

            # Se formatean las fechas de los intervalos
            df1.index = df1.index.strftime("%Y/%m/%d")

            # Se crea el objeto del developer que será enviado al frontend
            obj = {
                'name': developer,
                'dates': list(df1.index),
                'additions': list(df1['additions']),
                'commits': list(df2['additions'])
            }

            developers_info.append(obj)
    return developers_info


# Obtiene las fechas limites (minima y maxima) de desarrollo,
# es decir, cuando comenzo el desarrollo y hasta cuando han desarrollado
def get_github_min_max_date(team_project_id):
    docs = mongo.db.get_collection('github_repo_info').find({'team_project_id': team_project_id})
    df_docs = pd.DataFrame(list(docs))
    min_date = df_docs['timestamp'].min()
    max_date = df_docs['timestamp'].max()
    min_date = datetime.fromtimestamp(min_date).strftime('%Y-%m-%d %H:%M:%S')
    max_date = datetime.fromtimestamp(max_date).strftime('%Y-%m-%d %H:%M:%S')
    return min_date, max_date


###################################################################
###################### PARTICIPANTS NAMES #########################
###################################################################

# Obtiene los nombres de usuario de los desarrolladores que han participado en el desarrollo
# de cualquier proyecto (para saber quienes han aportado en alguno de los proyectos)
# Esto para saber quienes han aportado en la productividad grupal
def get_part_names(team_id, start, end):
    names_send = []
    if start != -1 and end != -1:
        projects = get_projects(team_id)
        for id in projects:
            names = get_developers_names(id, start, end)
            for name in names:
                if name['author'] not in names_send:
                    names_send.append(name['author'])
        return names_send
