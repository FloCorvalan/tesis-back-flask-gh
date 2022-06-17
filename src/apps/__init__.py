from flask import Flask
from database import database

from apps.github.views import github
from flask_cors import CORS

def create_app(config):
    app = Flask(__name__)
    CORS(app)
    # setup with the configuration provided
    app.config.from_object(config)
    
    # setup all our dependencies
    mongo = database.init_app(app)
    
    # register blueprint
    app.register_blueprint(github)
    
    return app, mongo