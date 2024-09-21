import datetime
import os


class Config:
    # TODO: Update this when you create a new project
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQLALCHEMY_DATABASE_URI")
        or "postgresql://sa:sa@localhost/awesomeapp"
    )
    # TODO: Update this when you create a new project
    # Generated from https://1password.com/password-generator with no Symbols and length as 20
    JWT_SECRET_KEY = "Q4MKrNZ6RJP9PV4iXBad"
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=60)
    # Query param with which you can pass JWT Token of the user if required
    JWT_QUERY_STRING_NAME = "token"
    BASE_API_URL = os.environ.get("BASE_API_URL") or "http://localhost:5001"
