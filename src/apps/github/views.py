from flask import Blueprint
from .methods import *

github = Blueprint('github', __name__)

@github.route('/github', methods=['GET'])
def test():
    return