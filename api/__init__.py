from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_class=Config):
    api = Flask(__name__)
    api.config.from_object(config_class)

    db.init_app(api)
    with api.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(db.select(1))
            print("Database connection successful")
        except Exception as e:
            print("Error connecting to database:", str(e))
            raise e

    migrate.init_app(api, db)

    jwt.init_app(api)

    from api.routes import parent_api_blueprint
    from api.routes.users import user_blueprint

    parent_api_blueprint.register_blueprint(user_blueprint)
    api.register_blueprint(parent_api_blueprint)

    return api
