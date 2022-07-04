from flask import Blueprint, Response, request
from .methods import *
import json
from bson import json_util

github = Blueprint('github', __name__)

###################################################################
########################## REGISTERS ##############################
###################################################################

@github.route('/github', methods=['POST'])
def get_registers_service():
    team_project_id = request.json['team_project_id']
    source_id = request.json['source_id']
    get_registers(team_project_id, source_id)
    return {'message': 'Successfully extracted data'}

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------

###################################################################
################### ALL PARTICIPATION PROCESS #####################
###################################################################

@github.route('/github/participation', methods=['POST'])
def get_github_participation():
    team_project_id = request.json['team_project_id']
    source_id = request.json['source_id']
    #team_project_id = '625f1e47bffb6a90d59d3e06'
    #source_id = '6255d136c04ac27bbad0276d'
    # Se obtiene la informacion general del repositorio (totales) y de los desarrolladores
    get_repo_info(team_project_id, source_id)

    # Se calculan los porcentajes de participacion de los desarrolladores
    calculate_percentages(team_project_id, source_id)

    # Se obtiene la participacion de los desarrolladores
    participation = get_participation_method(team_project_id, source_id)
    
    response = json_util.dumps(participation)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------

###################################################################
################### ALL PRODUCTIVITY PROCESS ######################
###################################################################

@github.route('/github/prod', methods=['POST'])
def get_github_productivity():
    team_project_id = request.json['team_project_id']

    # Se buscan las fechas min y max
    min_date_str, max_date_str = get_github_min_max_date(team_project_id)

    #min_date_str = '2022-03-21 05:23:38'
    min_date = datetime.strptime(str(min_date_str).split(".")[0], "%Y-%m-%d %H:%M:%S")
    #max_date_str = '2022-05-21 05:23:38'
    max_date = datetime.strptime(str(max_date_str).split(".")[0], "%Y-%m-%d %H:%M:%S")
    prod = get_prod_info(team_project_id, min_date, max_date)
    response = json_util.dumps(prod)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------

###################################################################
###################### PARTICIPANTS NAMES #########################
###################################################################

@github.route('/github/part-names', methods=['POST'])
def get_github_part_names():
    team_id = request.json['team_id']
    timestamps = request.json['timestamps']
    names = get_part_names(team_id, timestamps)
    response = json_util.dumps(names)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------