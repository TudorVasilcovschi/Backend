import logging
from http import HTTPStatus
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token

from database.database import Database
from src.database.db_queries import find_user_by_username, insert_new_user, generate_unique_user_id_str
import psycopg2.extras


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
                    is_dataset_user = row['is_dataset_user']
                    access_token = create_access_token(identity=user_id)
                    return {
                        'message': 'You are logged in successfully',
                        'access_token': access_token,
                        'is_dataset_user': is_dataset_user
                    }, HTTPStatus.OK
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
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            user_exists = find_user_by_username(conn, username)
            if user_exists:
                return {'message': 'Username already taken'}, HTTPStatus.CONFLICT

            hashed_password = generate_password_hash(password)
            user_id = generate_unique_user_id_str(cursor)
            insert_new_user(conn, user_id, username, hashed_password, False)

            access_token = create_access_token(identity=user_id)
            return {
                'message': 'User registered successfully',
                'access_token': access_token,
                'is_dataset_user': False
            }, HTTPStatus.CREATED
        except Exception as e:
            logging.error(f"Database error: {e}")
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            Database.return_connection(conn)

    @staticmethod
    def register_dataset_user(user_id, password="defaultpassword"):
        """
        This is meant to be called from postman, not the app
        """
        username = 'user_' + user_id

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
            insert_new_user(conn, user_id, username, hashed_password, True)

            return {
                'message': 'User registered successfully'
            }, HTTPStatus.CREATED
        except Exception as e:
            logging.error(f"Database error: {e}")
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            Database.return_connection(conn)