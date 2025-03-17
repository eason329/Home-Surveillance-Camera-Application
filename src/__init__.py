from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from decouple import config
from dotenv import load_dotenv
from flask_mail import Mail
from celery import Celery

load_dotenv()  # take environment variables from .env.

app = Flask(__name__)
app.config.from_object(config("APP_SETTINGS"))

email = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Registering blueprints
from .account.views import account
app.register_blueprint(account)

from .main.views import main
app.register_blueprint(main)

from .account.models import User

login_manager.login_view = "account.login"
login_manager.login_message_category = "danger"

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()
