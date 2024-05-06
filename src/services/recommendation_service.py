from http import HTTPStatus

import pandas as pd

from models.recommendation_model import Recommender
from database.database import Database
from services.library_service import LibraryService


class RecommendationService:
    def __init__(self):
        self.recommender = Recommender()

    # === cold start
    def _update_books_with_user_ownership(self, user_id, books_df):
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            # Get book IDs from the DataFrame as a list
            book_ids = books_df['book_id'].tolist()

            # Check if the list is not empty to prevent SQL syntax error
            if not book_ids:
                return books_df

            # Prepare a query string with placeholders for book IDs
            placeholders = ', '.join(['%s'] * len(book_ids))

            # Query to check if these book IDs are in the user's library
            query = f"""
                        SELECT book_id
                        FROM user_library
                        WHERE user_id = %s AND book_id IN ({placeholders})
                    """
            cursor.execute(query, [user_id] + book_ids)
            user_books = cursor.fetchall()

            # Convert the list of tuples to a set for faster lookup
            user_books_set = {book[0] for book in user_books}

            # Update 'user_has_book' in the DataFrame
            books_df['user_has_book'] = books_df['book_id'].apply(lambda x: x in user_books_set)

            return books_df
        except Exception as e:
            conn.rollback()  # Important to rollback if exception occurs
            print(f"Error updating book ownership: {e}")
        finally:
            cursor.close()
            Database.return_connection(conn)

    def get_top_book_average_rating(self, user_id):
        top_books_df = self.recommender.top_book_average_rating()
        return self._update_books_with_user_ownership(user_id, top_books_df)

    def get_top_short_books(self, user_id):
        top_books_df = self.recommender.top_short_books()
        return self._update_books_with_user_ownership(user_id, top_books_df)

    def get_top_paper_books(self, user_id):
        top_books_df = self.recommender.top_paper_books()
        return self._update_books_with_user_ownership(user_id, top_books_df)

    def get_top_e_books(self, user_id):
        top_books_df = self.recommender.top_e_books()
        return self._update_books_with_user_ownership(user_id, top_books_df)

    # === recommendations based on input
    def get_top_similar_title_books(self, title):
        try:
            results = self.recommender.top_similar_title_books(title)
            books = results.to_dict(orient='records')
            return {'books': books, 'message': 'Books fetched successfully'}, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR

    def get_top_similar_description_books(self, description):
        try:
            results = self.recommender.top_similar_description_books(description)
            books = results.to_dict(orient='records')
            return {'books': books, 'message': 'Books fetched successfully'}, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR

    def get_top_similar_reviews_books(self, book_id):
        try:
            results = self.recommender.top_similar_reviews_books(book_id)
            if results.empty:  # Check if the result is empty
                return {
                    'message': 'No similar reviews found for the given book ID.',
                    'books': [],
                }, HTTPStatus.OK  # Operation successful, but no data found

            books = results.to_dict(orient='records')
            return {
                'message': 'Similar review books fetched successfully.',
                'books': books,
            }, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {
                'message': 'Internal Server Error',
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    def get_top_users_choice_books(self, user_id):
        try:
            recs, liked_books = self.recommender.similar_user_df(user_id)
            if recs.empty or not liked_books:  # Check if the recommendations or liked books are empty
                return {
                    'message': 'No recommendations found for the given user ID.',
                    'books': [],
                }, HTTPStatus.OK  # Operation successful, but no data found

            recommendations = self.recommender.top_users_choice_books(recs, liked_books)
            if recommendations.empty:  # Check if the final recommendations are empty
                return {
                    'message': 'No top user choice books found.',
                    'books': [],
                }, HTTPStatus.OK

            books = recommendations.to_dict(orient='records')
            return {
                'message': 'Top user choice books fetched successfully.',
                'books': books,
            }, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {
                'message': 'Internal Server Error',
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    def get_content_recommendations(self, user_id):
        try:
            results = self.recommender.content_recommendation(str(user_id))
            if results.empty:  # Check if the result is empty
                return {
                    'message': 'No content recommendations for the given book ID.',
                    'books': [],
                }, HTTPStatus.OK  # Operation successful, but no data found

            books = results.to_dict(orient='records')
            return {
                'message': 'Content recommendations fetched successfully.',
                'books': books,
            }, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {
                'message': 'Internal Server Error',
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    # collab
    def get_user_similarity_recommendations(self, user_id):
        try:
            similar_users_refined = self.recommender.similar_users(user_id)
            if similar_users_refined.empty:  # Check if the recommendations or liked books are empty
                return {
                    'message': 'No recommendations found for the given user ID.',
                    'books': [],
                }, HTTPStatus.OK  # Operation successful, but no data found

            recommendations = self.recommender.user_similarity_recommendation(similar_users_refined)
            if recommendations.empty:  # Check if the final recommendations are empty
                return {
                    'message': 'No recommendations found.',
                    'books': [],
                }, HTTPStatus.OK

            books = recommendations.to_dict(orient='records')
            return {
                'message': 'Recommendations fetched successfully.',
                'books': books,
            }, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {
                'message': 'Internal Server Error',
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    def get_item_similarity_recommendations(self, book_id):
        try:
            results = self.recommender.item_similarity_recommendation(book_id)
            if results.empty:  # Check if the result is empty
                return {
                    'message': 'No recommendations for the given book ID.',
                    'books': [],
                }, HTTPStatus.OK  # Operation successful, but no data found

            books = results.to_dict(orient='records')
            return {
                'message': 'Recommendations fetched successfully.',
                'books': books,
            }, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {
                'message': 'Internal Server Error',
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    def get_svd_recommendations(self, user_id):
        try:
            results = self.recommender.svd_recommendation(user_id)
            if results.empty:  # Check if the result is empty
                return {
                    'message': 'No recommendations for the given user.',
                    'books': [],
                }, HTTPStatus.OK  # Operation successful, but no data found

            books = results.to_dict(orient='records')
            return {
                'message': 'Recommendations fetched successfully.',
                'books': books,
            }, HTTPStatus.OK
        except Exception as e:
            print(f"Service Error: {e}")
            return {
                'message': 'Internal Server Error',
            }, HTTPStatus.INTERNAL_SERVER_ERROR
