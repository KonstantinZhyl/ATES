from flask import Flask
from flask_login import LoginManager
from oauth2 import config_oauth
from models import db, User
from auth import auth as auth_blueprint
from main import main as main_blueprint


# init SQLAlchemy so we can use it later in our models
def create_app(config=None):
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret'
    app.config['OAUTH2_REFRESH_TOKEN_GENERATOR'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:steve808.@localhost:5432/postgres'

    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)
    setup_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    app.register_blueprint(main_blueprint)

    return app


def setup_app(app):
    # Create tables if they do not exist already
    # @app.before_first_request

    db.init_app(app)
    config_oauth(app)
    # app.register_blueprint(bp, url_prefix='')
