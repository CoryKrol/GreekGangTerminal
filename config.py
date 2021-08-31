import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secretz'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    GREEK_MAIL_SUBJECT_PREFIX = '[Greek Gang Terminal]'
    GREEK_MAIL_SENDER = 'Greek Gang Terminal Admin <GreekGangTerminal@example.com>'
    GREEK_ = os.environ.get('GREEK_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FOLLOWERS_PER_PAGE = os.environ.get('FOLLOWERS_PER_PAGE') or 50
    TRADES_PER_PAGE = os.environ.get('TRADES_PER_PAGE') or 10
    WATCHLIST_PER_PAGE = os.environ.get('WATCHLIST_PER_PAGE') or 10
    UPLOADED_PHOTOS_DEST = os.environ.get('UPLOADED_PHOTOS_DEST') or 'app/files/images'
    UPLOADED_PHOTOS_URL = os.environ.get('UPLOADED_PHOTOS_URL') or 'http://localhost:5000/files/images/'
    RESIZE_URL = os.environ.get('RESIZE_URL') or 'http://localhost:5000/files/images/'
    RESIZE_ROOT = os.environ.get('RESIZE_ROOT') or 'app/files/images/'
    RESIZE_TARGET_DIRECTORY = os.environ.get('RESIZE_TARGET_DIRECTORY') or 'resized-images'
    RESIZE_STORAGE_BACKEND = os.environ.get('RESIZE_STORAGE_BACKEND') or 'file'


    @staticmethod
    def init_app(app):
        """Not needed"""
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
