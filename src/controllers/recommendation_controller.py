import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.services.recommendation_service import RecommendationService
from src.validators.request_validator import request_validator

recommendation = Blueprint('recommendation', __name__, url_prefix='/recommend')
recommendation_service = RecommendationService()


@recommendation.route('/content-recommendations', methods=['GET'])
@jwt_required()
def get_content_recommendations():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify(
            {'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        response, status_code = recommendation_service.get_content_recommendations(user_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for user {user_id}: {str(e)}")
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/user-similarity-recommendations', methods=['GET'])
@jwt_required()
def get_user_similarity_recommendations():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify(
            {'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        response, status_code = recommendation_service.get_user_similarity_recommendations(user_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for user {user_id}: {str(e)}")
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/item-similarity-recommendations', methods=['GET'])
def get_item_similarity_recommendations():
    book_id = request.args.get('book_id', None)
    if not book_id:
        return jsonify({"message": "Book id parameter is required."}), HTTPStatus.BAD_REQUEST
    book_id = int(book_id)

    try:
        response, status_code = recommendation_service.get_item_similarity_recommendations(book_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for book {book_id}: {str(e)}")
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/svd-recommendations', methods=['GET'])
@jwt_required()
def get_svd_recommendations():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify(
            {'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        response, status_code = recommendation_service.get_svd_recommendations(user_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for user {user_id}: {str(e)}")
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/top-book-average-rating-recommendations', methods=['POST'])
@jwt_required()
def get_top_book_average_rating():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify(
            {'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        recommendations = recommendation_service.get_top_book_average_rating(user_id)
        return jsonify({
            "success": True,
            "recommendations": recommendations.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/top-short-books-recommendations', methods=['POST'])
@jwt_required()
def get_top_short_books():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify(
            {'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        recommendations = recommendation_service.get_top_short_books(user_id)
        return jsonify({
            "success": True,
            "recommendations": recommendations.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/top-paper-books-recommendations', methods=['POST'])
@jwt_required()
def get_top_paper_books():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify(
            {'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        recommendations = recommendation_service.get_top_paper_books(user_id)
        return jsonify({
            "success": True,
            "recommendations": recommendations.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/top-e-books-recommendations', methods=['POST'])
@jwt_required()
def get_top_e_books():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify(
            {'success': False, 'message': 'Session is invalid or expired ' + user_id}), HTTPStatus.UNAUTHORIZED

    try:
        recommendations = recommendation_service.get_top_e_books(user_id)
        return jsonify({
            "success": True,
            "recommendations": recommendations.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/top-similar-title-books', methods=['GET'])
def get_top_similar_title_books():
    title = request.args.get('title', None)  # Use request.args for query parameters
    if not title:
        return jsonify({"success": False, "message": "Title parameter is required."}), HTTPStatus.BAD_REQUEST

    try:
        response, status_code = recommendation_service.get_top_similar_title_books(title)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for title {title}: {str(e)}")
        return jsonify({"message": "Failed to generate recommendations."}),  HTTPStatus.INTERNAL_SERVER_ERROR


@recommendation.route('/top-similar-description-books', methods=['GET'])
def get_top_similar_description_books():
    description = request.args.get('description', None)
    if not description:
        return jsonify({"message": "Description parameter is required."}), HTTPStatus.BAD_REQUEST

    try:
        response, status_code = recommendation_service.get_top_similar_description_books(description)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for description {description}: {str(e)}")
        return jsonify({"message": "Failed to generate recommendations."}),  HTTPStatus.INTERNAL_SERVER_ERROR


@recommendation.route('/top-similar-reviews-books', methods=['GET'])
def get_top_similar_reviews_books():
    book_id = request.args.get('book_id', None)
    if not book_id:
        return jsonify({"message": "Book id parameter is required."}), HTTPStatus.BAD_REQUEST
    book_id = int(book_id)

    try:
        response, status_code = recommendation_service.get_top_similar_reviews_books(book_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for book_id {book_id}: {str(e)}")
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500


@recommendation.route('/top-users-choice-books', methods=['GET'])
@jwt_required()
def get_top_users_choice_books():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"message": "User id parameter is required."}), HTTPStatus.BAD_REQUEST

    try:
        response, status_code = recommendation_service.get_top_users_choice_books(user_id)
        return make_response(jsonify(response), status_code)
    except Exception as e:
        logging.error(f"Error processing recommendations for user {user_id}: {str(e)}")
        return jsonify({"success": False, "message": "Failed to generate recommendations."}), 500
