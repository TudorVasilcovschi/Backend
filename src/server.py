from dotenv import load_dotenv
import os
from database.database import Database

load_dotenv()

# Initialize the connection pool
database_args = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}
Database.initialize(**database_args)


import logging
from config import LOGGING_CONFIG
from flask import Flask
from flask_cors import CORS  # pip install -U flask-cors
from flask_jwt_extended import JWTManager
from datetime import timedelta
from src.controllers.recommendation_controller import recommendation as recommendation_blueprint
from src.controllers.auth_controller import auth as auth_blueprint
from src.controllers.library_controller import library as library_blueprint



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_key_for_dev')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.config['SESSION_COOKIE_NAME'] = 'cookie'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # You should also use HTTPS with this
app.config['JWT_SECRET_KEY'] = "mnbvcxz98765"
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)

CORS(app, supports_credentials=True)
jwt = JWTManager(app)

app.register_blueprint(recommendation_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(library_blueprint)

logging.basicConfig(**LOGGING_CONFIG)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
