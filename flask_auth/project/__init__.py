# __init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Init SQLAlchemy pour pouvoir l'utiliser dans les modèles
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # 🔐 Configuration
    app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init DB
    db.init_app(app)

    # Init LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Importer tous les modèles pour que db.create_all() crée toutes les tables
    from .models import User, Tweet, Like, Comment

    # User loader pour Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # ⚡ Créer la base et les tables si elles n’existent pas
    with app.app_context():
        print("DB path:", os.path.abspath("db.sqlite"))
        print("Création de la DB si elle n'existe pas...")
        db.create_all()
        print("DB prête !")

    return app
