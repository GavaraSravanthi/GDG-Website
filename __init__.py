from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail
from settings import Config
from .models import User

mongo = PyMongo()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        user_data = mongo.db.users.find_one({'_id': user_id})
        if user_data:
            return User(
                user_id=user_data['_id'],
                email=user_data['email'],
                password_hash=user_data['password'],  # ✅ comma added here
                is_admin=user_data.get('is_admin', False)
            )
        return None

    from .routes import main
    from .api import api
    app.register_blueprint(main)
    app.register_blueprint(api)
    return app

    #return app
