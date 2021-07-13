from clientlib.config import load_config
from clientlib.authentication import load_or_fetch_oauth2_token
from clientlib.exceptions import *
import requests
import json
import uuid
import urllib.parse
from .setup import CONFIG_FILE_LOCATION

def get_file(filepath: str, user: str = None, group: str = None):
    """Make a request to get a file from the HSM."""

    # get the config
    config = load_config()

    # get the default user if no user is supplied in parameters and default_user
    # exists in the config file
    if (user is None and
        "user" in config and
        "default_user" in config["user"]):
        user = config["user"]["default_user"]

    # get the default group if no group is supplied and default_group is in the
    # config file
    if (group is None and
        "user" in config and
        "default_group" in config["user"]):
        group = config["user"]["default_group"]


    # get an OAuth token and build the header with it in
    auth_token = load_or_fetch_oauth2_token(config, interactive = True)
    token_headers = {
        "Content-Type"  : "application/json",
        "cache-control" : "no-cache",
        "Authorization" : f"Bearer {auth_token['access_token']}"
    }

    # construct the url from the details in the config file
    url = urllib.parse.urljoin(config["server"]["url"],
                               "/".join([config["server"]["api"],
                               "files"])
                              )

    # build the parameters.  files/get requires:
    #    transaction_id: UUID
    #    user: str
    #    group: str
    # create the transaction ID
    transaction_id = uuid.uuid4()
    input_params = {"transaction_id" : transaction_id,
                    "user" : user,
                    "group" : group,
                    "filepath" : filepath}

    # make the requestv
    try:
        response = requests.get(
            url,
            headers = token_headers,
            params = input_params
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Could not connect to the URL: {url}\n"
            "Check the ['server']['url'] and ['server']['api'] setting in the "
            f"{CONFIG_FILE_LOCATION} file."
        )

    # process the response
    #    possible responses: 202, 400, 403, 404, 422.
    if (response.status_code == requests.codes.ok or
        response.status_code == requests.codes.accepted):
        response_json = response.json()
        print(response_json)
    elif (response.status_code == requests.codes.bad_request): # 400 error
        response_json = json.loads(response.json()['detail'])
        raise RequestError(
            f"Could not complete the request to the URL: {url} \n"
            f"{response_json['details']} (HTTP_{response.status_code})"
        )
    elif (response.status_code == requests.codes.forbidden):   # 403
        raise AuthenticationError(
            f"Could not complete the request to the URL: {url} \n"
            "Authentication failed.  Check that the token in the "
            f"{config['authentication']['oauth_token_file_location']} file "
            "is a valid token (HTTP_403)"
        )
    elif (response.status_code == requests.codes.not_found):   # 404
        response_json = json.loads(response.json()['detail'])
        raise RequestError(
            f"Could not complete the request to the URL: {url} \n"
            f"{response_json['msg']} (HTTP_{response.status_code})"
        )
    elif (response.status_code == requests.codes.unprocessable): # 422
        response_json = response.json()['detail'][0]
        raise RequestError(
            f"Could not complete the request to the URL: {url} \n"
            f"{response_json['msg']} (HTTP_{response.status_code})"
        )
    else:
        raise RequestError(
            f"Could not complete the request to the URL: {url} "
            f"(HTTP_{response.status_code})"
        )
