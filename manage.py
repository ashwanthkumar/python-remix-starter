from flask_migrate import Migrate

from api import create_app, db
from api.schema import User

app = create_app()
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
    }
