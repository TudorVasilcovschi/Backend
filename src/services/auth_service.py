import logging
from http import HTTPStatus
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token

from database.database import Database
from src.database.db_queries import find_user_by_username, insert_new_user


class AuthService:
    def __init__(self):
        pass

    @staticmethod
    def authenticate_user(username, password):
        conn = Database.get_connection()
        if not conn:
            return {'message': 'Database connection error'}, HTTPStatus.SERVICE_UNAVAILABLE

        try:
            row = find_user_by_username(conn, username)

            if row:
                if check_password_hash(row['password'], password):
                    user_id = row['id']
                    access_token = create_access_token(identity=user_id)
                    return {'message': 'You are logged in successfully', 'access_token': access_token}, HTTPStatus.OK
                else:
                    return {'message': 'Invalid password'}, HTTPStatus.UNAUTHORIZED
            else:
                return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
        except Exception as e:
            logging.error(f"Database error: {e}")
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            Database.return_connection(conn)

    @staticmethod
    def register_user(username, password):
        conn = Database.get_connection()
        if not conn:
            return {'message': 'Database connection error'}, HTTPStatus.INTERNAL_SERVER_ERROR

        try:
            # Check if the user already exists
            existing_user = find_user_by_username(conn, username)
            if existing_user:
                return {'message': 'Username already taken'}, HTTPStatus.CONFLICT

            # Hash the password and insert new user into the database.
            hashed_password = generate_password_hash(password)
            new_user_id = insert_new_user(conn, username, hashed_password)

            if new_user_id:
                access_token = create_access_token(identity=new_user_id)
                return {
                    'message': 'User registered successfully',
                    'access_token': access_token,
                }, HTTPStatus.CREATED
            else:
                return {'message': 'Registration failed'}, HTTPStatus.BAD_REQUEST

        except Exception as e:
            logging.error(f"Database error: {e}")
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            Database.return_connection(conn)
