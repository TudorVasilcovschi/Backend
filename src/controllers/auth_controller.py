from http import HTTPStatus

from flask import Blueprint, request, jsonify, make_response, session
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.validators.request_validator import request_validator
from src.services.auth_service import AuthService

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/register', methods=['POST'])
def register():
    _json, response, status_code = request_validator.validate_and_extract_payload(request, ['username', 'password'])

    if response is not None and status_code is not None:
        return jsonify({"success": False, "message": response["message"]}), status_code

    username = _json['username']
    password = _json['password']

    response, status_code = AuthService.register_user(username, password)
    if status_code == HTTPStatus.OK:
        return make_response(jsonify(response), status_code)
    else:
        # Clear the session in case of failed login attempts.
        session.pop('user_id', None)
        return make_response(jsonify(response), status_code)


@auth.route('/register_dataset_user', methods=['POST'])
def register_dataset_users():
    user_id = request.get_json().get('user_id')
    if not user_id:
        return jsonify({'message': 'No user IDs provided'}), HTTPStatus.BAD_REQUEST

    response, status_code = AuthService.register_dataset_user(user_id)
    return make_response(jsonify(response), status_code)


@auth.route('/login', methods=['POST'])
def login():
    _json, response, status_code = request_validator.validate_and_extract_payload(request, ['username', 'password'])

    if response is not None and status_code is not None:
        return jsonify({"success": False, "message": response["message"]}), status_code

    username = _json['username']
    password = _json['password']

    response, status_code = AuthService.authenticate_user(username, password)
    if status_code == HTTPStatus.OK:
        return make_response(jsonify(response), status_code)
    else:
        return make_response(jsonify(response), status_code)


@auth.route('/LOGOUT', methods=['POST'])
def logout():
    return make_response(jsonify({'message': "Logout successful"}))


@auth.route('/validate', methods=['GET'])
@jwt_required()
def validate():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'isAuthenticated': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED
    return jsonify({'isAuthenticated': True, 'message': 'Session is valid', 'user_id': user_id}), HTTPStatus.OK

