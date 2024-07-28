from flask import Flask
from app.routes import main as main_blueprint
from celery import Celery

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    app.register_blueprint(main_blueprint)
    return app

def create_celery_app(app=None):
    app = app or create_app()
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    celery.autodiscover_tasks(['app.tasks'])
    return celery
