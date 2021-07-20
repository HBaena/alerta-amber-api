from flask import Flask
from flask_restful import Api  # modules for fast creation of apis
from flask_jwt_extended import JWTManager

from DB import PosgresPoolConnection
from psycopg2 import pool

from datetime import timedelta
from os import path, getcwd
from notification_manager import NotificationsManager

from base64 import b64encode 


def init_notification_manager() -> NotificationsManager:
    return NotificationsManager(path.join(getcwd(), "notifications-config.json"))

def connect_to_db_from_json(filename: str) -> pool:
    return PosgresPoolConnection(path.join(getcwd(), filename))

logo_amber_b64 = b64encode(open(path.join(getcwd(), 'static', 'img', 'amber-logo.png'), 'rb').read()).decode('ascii')
logo_jalisco_b64 = b64encode(open(path.join(getcwd(), 'static', 'img', 'jalisco-logo.png'), 'rb').read()).decode('ascii')


pdf_options = {
    'page-size': 'Letter',
    'margin-top': '0.1in',
    'margin-right': '0.1in',
    'margin-bottom': '0.1in',
    'margin-left': '0.1in',
    'encoding': "UTF-8",
    'no-outline': None
}


# APP/SERVER
app = Flask(__name__)  # Creating flask app
app.secret_key = "gydasjhfuisuqtyy234897dshfbhsdfg83wt7"  # Secret key

# API
api = Api(app)  # Creating API object from flask app

# JWT
app.config['JWT_SECRET_KEY'] = 'Officiautlaboreincididunttemportemporsedauteexcepteurdoloreirure dolor.'
app.config['JWT_PUBLIC_KEY'] = 'Proidentin.Exconsectetur.Dolorauteincididuntreprehenderit.'
app.config['JWT_PRIVATE_KEY'] = 'Quinisiculpaveniam.Doloramet.Ullamcoinoccaecatofficiaquis.'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
jwt = JWTManager(app)