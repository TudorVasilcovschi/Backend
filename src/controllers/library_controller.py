from http import HTTPStatus

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.library_service import LibraryService

from src.validators.request_validator import request_validator

library = Blueprint('library', __name__, url_prefix='/library')


@library.route('/add-book', methods=['POST'])
@jwt_required()
def add_book_to_library():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    book_id = request.json.get('book_id')

    try:
        response, status_code = LibraryService.add_book_to_user_library(user_id, book_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        return jsonify(
            {"success": False, "message": "Failed to add book to library."}), HTTPStatus.INTERNAL_SERVER_ERROR


@library.route('/remove-book', methods=['DELETE'])
@jwt_required()
def remove_book_from_library():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    book_id = request.json.get('book_id')

    try:
        response, status_code = LibraryService.remove_book_from_user_library(user_id, book_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        return jsonify(
            {"success": False, "message": "Failed to remove book from library."}), HTTPStatus.INTERNAL_SERVER_ERROR


@library.route('/get-books', methods=['GET'])
@jwt_required()
def get_user_books_from_library():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        response, status_code = LibraryService.get_user_books_from_library(user_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        return jsonify(
            {"success": False, "message": "Failed to add book to library."}), HTTPStatus.INTERNAL_SERVER_ERROR


@library.route('/get-dataset-books', methods=['GET'])
@jwt_required()
def get_user_books_from_dataset():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        response, status_code = LibraryService.get_user_books_from_dataset(user_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        return jsonify(
            {"success": False, "message": "Failed to add book to dataset library."}), HTTPStatus.INTERNAL_SERVER_ERROR


@library.route('/get-books-by-title', methods=['GET'])
@jwt_required()
def get_filtered_books():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'success': False, 'message': 'Session is invalid or expired'}), HTTPStatus.UNAUTHORIZED

    title = request.args.get('title', None)  # Use request.args for query parameters

    if not title:
        return jsonify({"success": False, "message": "Title parameter is required."}), HTTPStatus.BAD_REQUEST

    try:
        response, status_code = LibraryService.search_books_by_title(user_id, title)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        return jsonify(
            {"success": False, "message": "Failed to add book to library."}), HTTPStatus.INTERNAL_SERVER_ERROR


