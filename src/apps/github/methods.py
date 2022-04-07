############################ ACTIVIDADES ############################
TEST = ['/test', '.test', '/tests']
CODE = ['.jar', '.py', '.java', '.php', '.vue', '.js', '.r', '.jsx', '.ts', '.go']

DIC = {
    "TEST":"TEST",
    "CODE":"CODE",
}

#####################################################################


if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo

from github import Github
from bson.objectid import ObjectId


def get_authenticated_user(source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    token = source['token']
    user = source['user']
    g = Github(token)
    return g.get_user(user)

def get_registers(team_id, source_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id)})
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    github_info = mongo.db.get_collection('github_info').find_one({'team_id': team_id, 'source_id': source_id})
    repo_name = source['name']
    case_id = team['actual_case_id']
    user = get_authenticated_user(source_id)

