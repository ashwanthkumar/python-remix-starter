from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from api import db
from api.schema import User

user_blueprint = Blueprint("users_v1", __name__, url_prefix="/user")


@user_blueprint.route("/user/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"email": user.email}), 201


@user_blueprint.route("/user/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Bad email or password"}), 401

    access_token = create_access_token(identity=user, fresh=True, expires_delta=False)

    return jsonify({"user_id": user.id, "token": access_token}), 200


@user_blueprint.route("/user/me", methods=["GET"])
@jwt_required()
def me():
    current_user = get_jwt_identity()
    user = User.query.get(current_user)

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"user_id": user.id, "email": user.email}), 200
