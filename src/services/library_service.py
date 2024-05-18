from http import HTTPStatus

from database.database import Database


class LibraryService:
    def __init__(self):
        pass

    @staticmethod
    def add_book_to_user_library(user_id, book_id):
        conn = Database.get_connection()
        if not conn:
            return {'message': 'Database connection error'}, HTTPStatus.SERVICE_UNAVAILABLE
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM user_library WHERE user_id = %s AND book_id = %s", (user_id, book_id))
            book_exists = cursor.fetchone()

            if book_exists:
                return {'message': 'Book is already in library'}, HTTPStatus.CONFLICT

            # Insert the new book into the user's library
            cursor.execute("INSERT INTO user_library (user_id, book_id) VALUES (%s, %s)", (user_id, book_id))
            conn.commit()

            # Retrieve the details of the added book
            cursor.execute("""
                        SELECT book_id, title_without_series, publication_year, publisher, average_rating, image_url, url, num_pages
                        FROM books
                        WHERE book_id = %s
                    """, (book_id,))
            book_details = cursor.fetchone()
            if book_details:
                return {
                    'book': {
                        'book_id': book_details[0],
                        'title_without_series': book_details[1],
                        'publication_year': book_details[2],
                        'publisher': book_details[3],
                        'average_rating': book_details[4],
                        'image_url': book_details[5],
                        'url': book_details[6],
                        'num_pages': book_details[7]
                    },
                    'message': 'Book added to library successfully'
                }, HTTPStatus.CREATED
            return {'book': {}, 'message': 'No book found'}, HTTPStatus.OK
        except Exception as e:
            conn.rollback()  # Important to rollback if exception occurs
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            cursor.close()  # Close the cursor
            Database.return_connection(conn)  # Return the connection back to the pool

    @staticmethod
    def remove_book_from_user_library(user_id, book_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        if not conn:
            return {'message': 'Database connection error'}, HTTPStatus.SERVICE_UNAVAILABLE

        try:
            # Check if the book exists in the user's library
            cursor.execute("SELECT * FROM user_library WHERE user_id = %s AND book_id = %s", (user_id, book_id))
            book_exists = cursor.fetchone()

            if not book_exists:
                return {'message': 'Book not found in library'}, HTTPStatus.NOT_FOUND

            # Delete the book from the user's library
            cursor.execute("DELETE FROM user_library WHERE user_id = %s AND book_id = %s", (user_id, book_id))
            conn.commit()

            return {'message': 'Book removed from library successfully'}, HTTPStatus.OK

        except Exception as e:
            conn.rollback()
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            cursor.close()
            Database.return_connection(conn)

    @staticmethod
    def get_user_books_from_library(user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        if not conn:
            return {'message': 'Database connection error'}, HTTPStatus.SERVICE_UNAVAILABLE

        try:
            query = "SELECT * FROM user_library WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            book_ids = cursor.fetchall()

            if not book_ids:
                return {'books': [], 'message': 'No books found'}, HTTPStatus.OK

            book_ids = [str(book_id[0]) for book_id in book_ids]
            book_ids_str = ','.join(book_ids)  # Convert list of book IDs to a string

            books_query = f"""
                        SELECT book_id, title_without_series, publication_year, publisher, average_rating, image_url, url, num_pages, is_ebook
                        FROM books
                        WHERE book_id IN ({book_ids_str})
                        """
            cursor.execute(books_query)
            books = cursor.fetchall()  # Fetches the book details

            books = [
                {'book_id': book[0],
                 'title_without_series': book[1],
                 'publication_year': book[2],
                 'publisher': book[3],
                 'average_rating': book[4],
                 'image_url': book[5],
                 'url': book[6],
                 'num_pages': book[7],
                 'is_ebook': book[8],  # this field for content recom
                 }
                for book in books
            ]

            return {'books': books, 'message': 'Books fetched successfully'}, HTTPStatus.OK

        except Exception as e:
            conn.rollback()  # Important to rollback if exception occurs
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            cursor.close()  # Close the cursor
            Database.return_connection(conn)

    @staticmethod
    def get_user_books_from_dataset(user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        if not conn:
            return {'message': 'Database connection error'}, HTTPStatus.SERVICE_UNAVAILABLE

        try:
            query = """
                SELECT book_id, title_without_series, publication_year,
                       publisher, average_rating, image_url, url, 
                       num_pages, is_ebook, review_text, rating
                FROM book_reviews
                WHERE user_id = %s
            """
            cursor.execute(query, (user_id,))
            books = cursor.fetchall()

            books_data = [
                {'book_id': book[0],
                 'title_without_series': book[1],
                 'publication_year': book[2],
                 'publisher': book[3],
                 'average_rating': book[4],
                 'image_url': book[5],
                 'url': book[6],
                 'num_pages': book[7],
                 'is_ebook': book[8],
                 'review_text': book[9],
                 'rating': book[10]
                 }
                for book in books
            ]

            return {'books': books_data, 'message': 'Books fetched successfully'}, HTTPStatus.OK

        except Exception as e:
            conn.rollback()  # Important to rollback if exception occurs
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            cursor.close()  # Close the cursor
            Database.return_connection(conn)

    @staticmethod
    def search_books_by_title(user_id, search_query):
        """
        Performs a search for books by title in a database, offering both exact and wildcard search modes.
        It is designed to return a list of books that match the search criteria, along with their details and whether
        the user already has the book in their library.
        :param user_id: The user's ID for whom the search is conducted.
        :param search_query: The title or part of the title to search for.
        :return: A dictionary with a list of matched books and a status message, accompanied by an HTTP status code.
        """
        conn = Database.get_connection()
        cursor = conn.cursor()
        if not conn:
            return {'message': 'Database connection error'}, HTTPStatus.SERVICE_UNAVAILABLE

        books = []
        try:
            if not search_query:
                return {'message': 'Search query is empty'}, HTTPStatus.BAD_REQUEST

            books_query = f"""
                            SELECT b.book_id, b.title_without_series, b.publication_year, b.publisher, b.average_rating, b.image_url, b.url, b.num_pages,
                            ul.book_id IS NOT NULL AS user_has_book
                            FROM books b
                            LEFT JOIN user_library ul ON b.book_id = ul.book_id AND ul.user_id = %s
                            WHERE b.title_without_series ~* %s
                            """
            search_pattern = fr"\m{search_query}\M"
            cursor.execute(books_query, (user_id, search_pattern))
            books = cursor.fetchall()

            if not books:
                return {'books': [], 'message': 'No books found'}, HTTPStatus.OK

            books = [
                {'book_id': book[0],
                 'title_without_series': book[1],
                 'publication_year': book[2],
                 'publisher': book[3],
                 'average_rating': book[4],
                 'image_url': book[5],
                 'url': book[6],
                 'num_pages': book[7],
                 'user_has_book': book[8]
                 }
                for book in books
            ]

            return {'books': books, 'message': 'Books fetched successfully'}, HTTPStatus.OK

        except Exception as e:
            conn.rollback()  # Important to rollback if an exception occurs
            return {'message': 'Internal Server Error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            cursor.close()  # Close the cursor
            Database.return_connection(conn)