from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_oauthlib.provider import OAuth2Provider
from flasgger import Swagger

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TESTING'] = False
app.config.from_pyfile('config/config_db.py')
app.config.from_pyfile('config/config_security.py')
app.config.from_pyfile('config/config_mail.py')
app.config.from_pyfile('config/config_swagger.py')
db = SQLAlchemy(app)
oauth = OAuth2Provider(app)
Swagger(app)

HOME_URL = "http://ec2-54-160-178-89.compute-1.amazonaws.com/"
ENCRYPTION_METHOD = 'pbkdf2:sha1'

from flask_app.routes import *
from flask_app.oauth2 import *

if __name__ == '__main__':
    app.run()