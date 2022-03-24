import os
import pytest
import requests
import json
import nlds_client.clientlib.authentication as clau
import nlds_client.clientlib.config as clcnf
import nlds_client.clientlib.exceptions as exc
import dotenv
import copy

# Load environment files from .env file
dotenv.load_dotenv()

TEST_USERNAME = os.environ['USERNAME']
TEST_PASSWORD = os.environ['PASSWORD']
TEST_TOKEN_TEXT = os.environ['TOKEN_TEXT']
TEST_CONFIG_FILE = os.environ.get('CONFIG_FILE')
EDGE_VALUES = ['', None, ' ',]

@pytest.fixture
def basic_config():
    # Read the template config file into a json object
    config_filename = os.path.join(os.path.dirname(__file__), '../nlds_client/templates/nlds-config.j2')
    fh = open(config_filename)
    return json.load(fh)

@pytest.fixture
def functional_config():
    # Read the users actual config file so test calls can be made to the API
    if TEST_CONFIG_FILE is None:
        return clcnf.load_config()
    else:
        fh = open(TEST_CONFIG_FILE)
        return json.load(fh)

class MockResponse:
    # A mock response object for checking error handling capabilities
    def __init__(self, status_code=200, text=TEST_TOKEN_TEXT):
        self.status_code = status_code
        self.text = text

def test_get_username_password(monkeypatch, basic_config):
    # Mock the username and password getting by overriding the input and getpass functions
    monkeypatch.setattr('builtins.input', lambda _: TEST_USERNAME)
    monkeypatch.setattr('getpass.getpass', lambda _: TEST_PASSWORD)

    userpswd_output = clau.get_username_password(basic_config)

    assert len(userpswd_output) == 2
    assert userpswd_output[0] == TEST_USERNAME
    assert userpswd_output[1] == TEST_PASSWORD

@pytest.mark.parametrize("status_code", [
    requests.codes.bad_request,
    requests.codes.unauthorized,
    requests.codes.forbidden,
    requests.codes.not_found,
    None, 
])
def test_process_fetch_oauth2_token_response(basic_config, status_code):
    clau.process_fetch_oauth2_token_response(basic_config, MockResponse(status_code=200))
    with pytest.raises(exc.StatusCodeError):
        clau.process_fetch_oauth2_token_response(basic_config, MockResponse(status_code=status_code))
        
    
@pytest.mark.parametrize("test_value", EDGE_VALUES)
def test_fetch_oauth_token(functional_config, test_value):
    # Test correct username and password
    token = clau.fetch_oauth2_token(functional_config, TEST_USERNAME, TEST_PASSWORD)
    assert isinstance(token, dict)
    
    # Test incorrect password raises exception
    with pytest.raises(exc.RequestError):
        clau.fetch_oauth2_token(functional_config, TEST_USERNAME, 'incorrect_password')
        clau.fetch_oauth2_token(functional_config, TEST_USERNAME, test_value)
    # Test incorrect/invalid user raises exception
    with pytest.raises(exc.RequestError):
        clau.fetch_oauth2_token(functional_config, 'invalid_user', TEST_PASSWORD)
        clau.fetch_oauth2_token(functional_config, test_value, TEST_PASSWORD)
    # Test incorrect user & password raises exception. 
    with pytest.raises(exc.StatusCodeError):
        clau.fetch_oauth2_token(functional_config, test_value, test_value)

@pytest.mark.parametrize("test_value", EDGE_VALUES)
def test_fetch_oauth_config(monkeypatch, functional_config, test_value):
    monkeypatch.setattr(clau, 'save_token', None)

    modified_config = copy.deepcopy(functional_config)
    modified_config['authentication']['oauth_client_id'] = test_value
    with pytest.raises(Exception):
        clau.fetch_oauth2_token(functional_config, TEST_USERNAME, TEST_PASSWORD)
        

    modified_config = copy.deepcopy(functional_config)
    modified_config['authentication']['oauth_client_secret'] = test_value
    with pytest.raises(Exception):
        clau.fetch_oauth2_token(functional_config, TEST_USERNAME, TEST_PASSWORD)
    
