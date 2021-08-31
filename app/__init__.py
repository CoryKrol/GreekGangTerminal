from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_whooshee import Whooshee
from flask_resize import Resize
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES

from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
photos = UploadSet('photos', IMAGES)
resize = Resize()
whooshee = Whooshee()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Must prefix route with the auth blueprint namespace


def create_app(config_name):
    """
    Application factory
    :param config_name: name of configuration to use
    :return: configured application instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    configure_uploads(app, [photos])
    resize.init_app(app)
    # whooshee = Whooshee(app)
    whooshee.init_app(app)
    # whooshee.reindex()

    # attach routes & error handlers to application here
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .stocks import stocks as stocks_blueprint
    app.register_blueprint(stocks_blueprint, url_prefix='/stocks')

    from .trades import trades as trades_blueprint
    app.register_blueprint(trades_blueprint, url_prefix='/trades')

    from .users import users as users_blueprint
    app.register_blueprint(users_blueprint, url_prefix='/users')

    return app
