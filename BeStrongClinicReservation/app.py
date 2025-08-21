from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
from flask_babel import Babel
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONNECTION_NAME = os.getenv('DB_CONNECTION_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
PROJECT_ID = os.getenv('PROJECT_ID')
INSTANCE_NAME = os.getenv('INSTANCE_NAME')
REGION = os.getenv('REGION')

app = Flask(__name__)
CORS(app)
app.secret_key = 'HJGFGHF^&%^&&*^&*YUGHJGHJF^%&YYHB'

if os.getenv('FLASK_DEPLOYMENT') == "production":
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{quote(DB_PASSWORD)}@{DB_HOST}/{DB_NAME}?unix_socket=/cloudsql/{PROJECT_ID}:{REGION}:{INSTANCE_NAME}"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{quote(DB_PASSWORD)}@{DB_HOST}/{DB_NAME}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 6
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['TESTING'] = True

db = SQLAlchemy(app)

login = LoginManager(app=app)

babel = Babel(app)
