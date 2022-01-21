import os
import unittest
from unittest.mock import patch
import nlds_client.clientlib.authentication as clau
import json
import requests 
import nlds_client.clientlib.exceptions as exc

TEST_USERNAME = 'testuser'
TEST_PASSWORD = 'testpswd'
TEST_TOKEN_TEXT = '{"access_token": "pojp", "expires_in": 36000, "token_type": "Bearer", "scope": "test scope", "refresh_token": "popojp"}'

class MockResponse:
    def __init__(self, status_code, text=TEST_TOKEN_TEXT):
        self.status_code = status_code
        self.text = text


def mock_requests_post(*args, **kwargs):
    if kwargs['data']['username'] == TEST_USERNAME and kwargs['data']['password'] == TEST_PASSWORD:
        return MockResponse(requests.codes.ok)
    elif kwargs['data']['username'] == TEST_USERNAME and kwargs['data']['password'] != TEST_PASSWORD:
        return MockResponse(requests.codes.unauthorized)
    elif kwargs['data']['username'] != TEST_USERNAME:
        return MockResponse(requests.codes.forbidden)


class TestAuthentication(unittest.TestCase):
    def setUp(self) -> None:
        template_filename = os.path.join(os.path.dirname(__file__), '../templates/nlds-config.j2')
        fh = open(template_filename)
        self.config = json.load(fh)
    
    def test_response_ok(self):
        response = MockResponse(requests.codes.ok)
        self.assertEqual(clau.process_fetch_oauth2_token_response(self.config, response), 
                         response)
    
    def test_response_bad_request(self):
        response = MockResponse(requests.codes.bad_request)
        with self.assertRaises(exc.RequestError):
            clau.process_fetch_oauth2_token_response(self.config, response)

    def test_response_unauthorised(self):
        response = MockResponse(requests.codes.unauthorized)
        with self.assertRaises(exc.AuthenticationError):
            clau.process_fetch_oauth2_token_response(self.config, response)

    def test_response_forbidden(self):
        response = MockResponse(requests.codes.forbidden)
        with self.assertRaises(exc.AuthenticationError):
            clau.process_fetch_oauth2_token_response(self.config, response)

    def test_response_not_found(self):
        response = MockResponse(requests.codes.not_found)
        with self.assertRaises(exc.RequestError):
            clau.process_fetch_oauth2_token_response(self.config, response)

    def test_response_undefined(self):
        response = MockResponse(None)
        with self.assertRaises(exc.RequestError):
            clau.process_fetch_oauth2_token_response(self.config, response)

    @patch('requests.post', side_effect=mock_requests_post)
    def test_fetch(self, mock_post):
        self.assertEqual(clau.fetch_oauth2_token(self.config, TEST_USERNAME, TEST_PASSWORD), json.loads(TEST_TOKEN_TEXT))
        with self.assertRaises(exc.AuthenticationError):
            clau.fetch_oauth2_token(self.config, TEST_USERNAME, '')
        with self.assertRaises(exc.AuthenticationError):
            clau.fetch_oauth2_token(self.config, '', TEST_PASSWORD)

if __name__ == '__main__':
    unittest.main()
