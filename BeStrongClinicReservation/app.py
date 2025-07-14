from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
from flask_babel import Babel
from flask_cors import CORS
import os

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')
DB_NAME = os.getenv('DB_NAME', 'OnlineAppointmentSystem')

app = Flask(__name__)
CORS(app)
app.secret_key = 'HJGFGHF^&%^&&*^&*YUGHJGHJF^%&YYHB'
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{quote(DB_PASSWORD)}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 6
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

db = SQLAlchemy(app)

login = LoginManager(app=app)

babel = Babel(app)
