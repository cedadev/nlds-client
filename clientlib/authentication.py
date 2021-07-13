import click
import requests
from requests_oauthlib import OAuth2Session
import json
import os.path

def get_username_password(auth_config):
    """Get the username and password interactively from the user.
       Print a message first to reassure the user.
    """
    click.echo("This application uses OAuth2 to authenticate with the server on"
               " your behalf.")
    click.echo("To do this it needs your username and password.")
    click.echo("Your password is not stored.  It is used to obtain an access "
               "token, which is stored in the file: "
               f"{auth_config['oauth_token_file_location']}")
    username = click.prompt("Username", type=str)
    password = click.prompt("Password", type=str, hide_input=True)
    return username, password


def fetch_oauth2_token(config, username, password):
    """Contact the OAuth2 token server using the URL in:
        config['authentication'][oauth_token_url]
    using the app and user details from:
        config['authentication']['oauth_client_id'],
        config['authentication']['oauth_client_secret'],
        username,
        password
    to obtain an access token.
    """
    # subset the config to the authentication section
    auth_config = config['authentication']
    token_headers = {
        "Content-Type" : "application/x-www-form-urlencoded",
        "cache-control": "no-cache",
    }
    token_data = {
        "client_id" : auth_config['oauth_client_id'],
        "client_secret" : auth_config['oauth_client_secret'],
        "username" : username,
        "password" : password,
        "grant_type" : "password",
        "scope" : f"{auth_config['oauth_scopes']}"
    }
    # contact the oauth_token_url to get a token, we expect a 200 status code to
    # be returned
    response = requests.post(
        auth_config['oauth_token_url'],
        data = token_data,
        headers = token_headers
    )

    if response.status_code == requests.codes['ok']:  # status code 200
        # save the token details
        token = json.loads(response.text)
        try:
            token_file = os.path.expanduser(
                auth_config['oauth_token_file_location']
            )
            fh = open(token_file, "w")
            json.dump(token, fh)
            fh.close()
        except FileNotFoundError:
            raise click.FileError(
                auth_config['oauth_token_file_location'],
                "The OAuth2 token file cannot be written to."
            )
    elif response.status_code == requests.codes['bad_request']: # code 400
        raise click.UsageError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            "Check your username and password and try again. (HTTP_400)"
        )
    elif response.status_code == requests.codes['unauthorized']:   # code 401
        raise click.UsageError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            "The request was unauthorized.\n"
            "Check the ['authentication']['oauth_client_id'] and "
            "['authentication']['oauth_client_secret'] settings in the "
            "~/.ceda-nlds-config file. (HTTP_401)"
        )
    elif response.status_code == requests.codes['forbidden']:   # code 403
        raise click.UsageError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            "Access is forbidden. (HTTP_403)"
        )
    elif response.status_code == requests.codes['not_found']:   # code 404
        raise click.UsageError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}\n"
            "The token server was not found.\n"
            "Check the ['authentication']['oauth_token_url'] setting in the "
            "~/.ceda-nlds-config file. (HTTP_404)"
        )
    else:
        raise click.UsageError(
            "Could not obtain an Oauth2 token from "
            f"{auth_config['oauth_token_url']}. (HTTP_{response.status_code})"
        )
    return token


def load_or_fetch_oauth2_token(config, interactive = True,
                               username = None, password = None):
    """Get an OAuth2 token, either from a file, or from the JASMIN SLCS
        server.
       A file containing the token is searched for at:
           config['authentication']['oauth_token_file_location']
       If this is not found then the user is asked to enter their username
        and password.  These are then used to obtain a token from the url at:
           config['authentication']['oauth_token_url'],
        using the app details from
           config['authentication']['oauth_client_id'],
           config['authentication']['oauth_client_secret']
    """
    # subset the config to the authentication section
    auth_config = config['authentication']
    try:
        # Open the token file and load it in
        token_file = os.path.expanduser(
            auth_config['oauth_token_file_location']
        )
        fh = open(token_file)
        token = json.load(fh)
        fh.close()
    except FileNotFoundError:
        # get the user name and password from the user interactively
        # or rely on parameters passed in
        if interactive:
            username, password = get_username_password(auth_config)
        token = fetch_oauth2_token(config, username, password)
    return token
