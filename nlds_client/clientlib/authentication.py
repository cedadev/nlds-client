import requests
from requests_oauthlib import OAuth2Session
import json
import os.path
import getpass
from nlds_client.clientlib.exceptions import *


def get_username_password(config):
    """Get the username and password interactively from the user.
       Print a message first to reassure the user.

    :param config: the configuration loaded by config.load_config
    :type config: Dict

    :return: a tuple containing (username, password)
    :rtype: Tuple

    """
    auth_config = config["authentication"]
    print(
        "This application uses OAuth2 to authenticate with the server on your"
        " behalf."
    )
    print("To do this it needs your username and password.")
    print(
        "Your password is not stored.  It is used to obtain an access token, "
        "which is stored in the file: "
        f"{auth_config['oauth_token_file_location']}"
    )
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    return username, password


def process_fetch_oauth2_token_response(config, response):
    """Process the return from fetching either a new token or from using the
    refresh token of an existing token to get a new token.

    :param config: the configuration loaded by config.load_config
    :type config: Dict

    :return: A requests response object, if none of the exceptions are
    triggered.
    :rtype: requests.models.Response object

    """
    auth_config = config["authentication"]

    if response.status_code == requests.codes.ok:  # status code 200
        return response
    elif response.status_code == requests.codes.bad_request:  # code 400
        raise RequestError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            "Check your username and password and try again. "
            f"(HTTP_{response.status_code})",
            response.status_code,
        )
    elif response.status_code == requests.codes.unauthorized:  # code 401
        raise AuthenticationError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            "The request was unauthorized.\n"
            "Check the ['authentication']['oauth_client_id'] and "
            "['authentication']['oauth_client_secret'] settings in the "
            f"~/.nlds-config file. (HTTP_{response.status_code})",
            response.status_code,
        )
    elif response.status_code == requests.codes.forbidden:  # code 403
        raise AuthenticationError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            f"Access is forbidden. (HTTP_{response.status_code})",
            response.status_code,
        )
    elif response.status_code == requests.codes.not_found:  # code 404
        raise RequestError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            "The token server was not found.\n"
            "Check the ['authentication']['oauth_token_url'] setting in the "
            f"~/.nlds-config file. (HTTP_{response.status_code})",
            response.status_code,
        )
    else:
        raise RequestError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}. (HTTP_{response.status_code})",
            response.status_code,
        )

    return response


def fetch_oauth2_token(config, username, password):
    """Contact the OAuth2 token server using the URL in:
        config['authentication'][oauth_token_url]
    using the app and user details from:
        config['authentication']['oauth_client_id'],
        config['authentication']['oauth_client_secret'],
        username,
        password
    to obtain an access token.

    :param config: the configuration loaded by config.load_config
    :type config: Dict

    :param username: username for password-flow OAuth
    :type username: string

    :param password: password for password-flow OAuth
    :type password: string

    :return: A Dictionary containing the token details
    :rtype: Dict

    """
    # subset the config to the authentication section
    auth_config = config["authentication"]
    # build the headers and body needed for the request
    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "cache-control": "no-cache",
    }
    token_data = {
        "client_id": auth_config["oauth_client_id"],
        "client_secret": auth_config["oauth_client_secret"],
        "username": username,
        "password": password,
        "grant_type": "password",
        "scope": f"{auth_config['oauth_scopes']}",
    }
    # contact the oauth_token_url to get a token, we expect a 200 status code to
    # be returned
    response = requests.post(
        auth_config["oauth_token_url"], data=token_data, headers=token_headers
    )
    # determine if any errors occurred
    process_fetch_oauth2_token_response(config, response)
    # save the token details after converting to JSON
    token = json.loads(response.text)
    save_token(config, token)
    return token


def fetch_oauth2_token_from_refresh(config):
    """Get a new token using the refresh token from an existing bearer token.
    The refresh token will be loaded from the existing token.

    :param config: the configuration loaded by config.load_config
    :type config: Dict

    :return: the token Dictionary
    :rtype: Dict

    """
    auth_config = config["authentication"]

    # load the OAuth token and get the refresh token
    token = load_token(config)

    try:
        refresh_token = token["refresh_token"]
    except KeyError:
        raise RequestError(
            "Could not obtain a refresh token from the token file at "
            f"{auth_config['oauth_token_file_location']}: it does not contain "
            "the 'refresh_token' key.",
            None,
        )

    # subset the config to the authentication section
    auth_config = config["authentication"]
    # build the headers and body needed for the request
    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "cache-control": "no-cache",
    }
    token_data = {
        "client_id": auth_config["oauth_client_id"],
        "client_secret": auth_config["oauth_client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": f"{auth_config['oauth_scopes']}",
    }
    # contact the oauth_token_url to get a token, we expect a 200 status code to
    # be returned
    response = requests.post(
        auth_config["oauth_token_url"], data=token_data, headers=token_headers
    )
    # determine if any errors occurred
    process_fetch_oauth2_token_response(config, response)
    # save the token details after converting to JSON
    token = json.loads(response.text)
    save_token(config, token)
    return token


def load_token(config):
    """Load the OAuth2 token from a file

    :param config: the configuration loaded by config.load_config
    :type config: Dict

    :raises FileNotFoundError: if the token file could not be found or read

    :return: the token Dictionary or False
    :rtype: Dict | False

    """
    # subset the config to the authentication section
    auth_config = config["authentication"]
    try:
        # Open the token file and load it in
        token_file = os.path.expanduser(auth_config["oauth_token_file_location"])
        fh = open(token_file)
        token = json.load(fh)
        fh.close()
        return token
    except FileNotFoundError:
        raise FileNotFoundError(
            "The OAuth2 token file cannot be read from: "
            f"{auth_config['oauth_token_file_location']}"
        )


def save_token(config, token):
    """Save the OAuth2 token to a file
    :param : the configuration loaded by config.load_config
    :type config: Dict

    :raises FileNotFoundError: if the token file could not be written to

    :return: None

    """
    auth_config = config["authentication"]

    try:
        token_file = os.path.expanduser(auth_config["oauth_token_file_location"])
        fh = open(token_file, "w")
        json.dump(token, fh)
        fh.close()
    except FileNotFoundError:
        raise FileNotFoundError(
            "The OAuth2 token file cannot be written to: "
            f"{auth_config['oauth_token_file_location']}"
        )
