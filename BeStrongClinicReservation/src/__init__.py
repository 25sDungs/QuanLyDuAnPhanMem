from flask import Flask
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
from flask_babel import Babel
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config[
    "SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/bestrongclinicreservation?charset=utf8mb4" % quote(
    'P@ssw0rd')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 6
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

db = SQLAlchemy(app)

login = LoginManager(app=app)

babel = Babel(app)
