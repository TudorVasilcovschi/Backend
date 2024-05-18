import unittest
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from services.auth_service import AuthService


class TestAuthService(unittest.TestCase):
    def setUp(self):
        # Mocking database connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Patching database connection and return connection methods
        self.patcher_get = patch('services.auth_service.Database.get_connection')
        self.patcher_return = patch('services.auth_service.Database.return_connection')
        self.mock_get_connection = self.patcher_get.start()
        self.mock_return_connection = self.patcher_return.start()
        self.mock_get_connection.return_value = self.mock_conn

        # Patching external dependencies in AuthService
        self.patch_find_user = patch('services.auth_service.find_user_by_username')
        self.patch_check_password = patch('services.auth_service.check_password_hash')
        self.patch_create_token = patch('services.auth_service.create_access_token')
        self.patch_generate_password = patch('services.auth_service.generate_password_hash')
        self.patch_insert_user = patch('services.auth_service.insert_new_user')
        self.patch_generate_id = patch('services.auth_service.generate_unique_user_id_str')

        # Starting patches and setting them to instance variables
        self.mock_find_user = self.patch_find_user.start()
        self.mock_check_password = self.patch_check_password.start()
        self.mock_create_token = self.patch_create_token.start()
        self.mock_generate_password = self.patch_generate_password.start()
        self.mock_insert_user = self.patch_insert_user.start()
        self.mock_generate_id = self.patch_generate_id.start()

        # Adding cleanup to stop patchers
        self.addCleanup(self.patcher_get.stop)
        self.addCleanup(self.patcher_return.stop)
        self.addCleanup(self.patch_find_user.stop)
        self.addCleanup(self.patch_check_password.stop)
        self.addCleanup(self.patch_create_token.stop)
        self.addCleanup(self.patch_generate_password.stop)
        self.addCleanup(self.patch_insert_user.stop)
        self.addCleanup(self.patch_generate_id.stop)

        # Initialize the AuthService instance
        self.service = AuthService()

    def test_authenticate_user_valid_login(self):
        self.mock_find_user.return_value = {'id': '123', 'password': 'hashed_password', 'is_dataset_user': False}
        self.mock_check_password.return_value = True
        self.mock_create_token.return_value = 'token'
        response, status = self.service.authenticate_user('user', 'password')
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(response['access_token'], 'token')
        self.assertFalse(response['is_dataset_user'])

    def test_authenticate_user_invalid_password(self):
        self.mock_find_user.return_value = {'id': '123', 'password': 'hashed_password', 'is_dataset_user': False}
        self.mock_check_password.return_value = False
        response, status = self.service.authenticate_user('user', 'wrong_password')
        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertIn('Invalid password', response['message'])

    def test_authenticate_user_user_not_found(self):
        self.mock_find_user.return_value = None
        response, status = self.service.authenticate_user('unknown_user', 'password')
        self.assertEqual(status, HTTPStatus.NOT_FOUND)
        self.assertIn('User not found', response['message'])

if __name__ == '__main__':
    unittest.main()
