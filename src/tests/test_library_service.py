import unittest
from unittest.mock import patch, MagicMock
from http import HTTPStatus

from services.library_service import LibraryService

import unittest
from unittest.mock import patch, MagicMock
from http import HTTPStatus

from services.library_service import LibraryService


class TestLibraryService(unittest.TestCase):

    def setUp(self):
        # Setup the mock database connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Patch the database connection methods used in LibraryService
        self.patcher_get = patch('services.library_service.Database.get_connection')
        self.patcher_return = patch('services.library_service.Database.return_connection')
        self.mock_get_connection = self.patcher_get.start()
        self.mock_return_connection = self.patcher_return.start()

        self.mock_get_connection.return_value = self.mock_conn
        self.mock_return_connection.return_value = None  # or setup as needed for specific tests

        # Ensure the patchers are stopped after tests
        self.addCleanup(self.patcher_get.stop)
        self.addCleanup(self.patcher_return.stop)

        # Initialize the LibraryService instance
        self.service = LibraryService()

    def test_add_book_to_user_library_no_connection(self):
        # Simulate a database connection failure
        self.mock_get_connection.return_value = None
        response, status = self.service.add_book_to_user_library(1, 1)
        self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertEqual(response['message'], 'Database connection error')

    def test_add_book_to_user_library_book_exists(self):
        # Test the scenario where the book already exists in the library
        self.mock_cursor.fetchone.return_value = (1, 1)
        response, status = self.service.add_book_to_user_library(1, 1)
        self.assertEqual(status, HTTPStatus.CONFLICT)
        self.assertEqual(response['message'], 'Book is already in library')

    def test_add_book_to_user_library_success(self):
        # Test successfully adding a book
        self.mock_cursor.fetchone.side_effect = [None, (1, 'Book Title', 2021, 'Publisher', 4.5, 'image_url', 'url', 300)]
        response, status = self.service.add_book_to_user_library(1, 1)
        self.assertEqual(status, HTTPStatus.CREATED)
        self.assertDictEqual(response['book'], {
            'book_id': 1,
            'title_without_series': 'Book Title',
            'publication_year': 2021,
            'publisher': 'Publisher',
            'average_rating': 4.5,
            'image_url': 'image_url',
            'url': 'url',
            'num_pages': 300
        })
        self.assertEqual(response['message'], 'Book added to library successfully')

    def test_add_book_to_user_library_failure(self):
        # Test handling of a general exception
        self.mock_cursor.execute.side_effect = Exception("Some error")
        response, status = self.service.add_book_to_user_library(1, 1)
        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(response['message'], 'Internal Server Error')

    # Additional tests for remove_book_from_user_library, get_user_books_from_library, etc.

if __name__ == '__main__':
    unittest.main()
