import requests
import json
import uuid
import urllib.parse

from typing import List, Dict

from clientlib.config import load_config, get_user, get_group
from clientlib.authentication import load_or_fetch_oauth2_token
from clientlib.exceptions import ConnectionError, RequestError, \
                                 AuthenticationError, ServerError

from .setup import CONFIG_FILE_LOCATION


def construct_server_url(config: Dict):
    """Construct the url from the details in the config file.
    :param config: dictionary of key:value pairs returned from the load_config
    function.
    :type config: Dict

    :return: a fully qualified url to the server hosting the REST API for NLDS.
    :rtype: string
    """
    url = urllib.parse.urljoin(config["server"]["url"],
                               "/".join([config["server"]["api"],
                               "files"])
                              )
    return url


def process_response(response: requests.models.Response, url: str):
    """Process the response to raise exceptions for errors or return the
    response result.
    :param response: response from the requests method (put, get, post, delete
    etc.)
    :type response: requests.models.Response
    :param url: the url from the construct_server_url function, required
    to format error messages
    :type url: string

    :raises RequestError: the request to the REST API is ill-formed
    :raises AuthenticationError: the user is not authorised to access the REST
    API or the data they are trying to access
    :raises ServerError: something is wrong with the server

    :return: A requests response object, if non of the exceptions are triggered.
    :rtype: requests.models.Response object
    """
    #    possible responses: 202, 400, 403, 404, 422.
    try:
        if (response.status_code == requests.codes.ok or
            response.status_code == requests.codes.accepted):
            return response
        elif (response.status_code == requests.codes.bad_request): # 400 error
            response_json = json.loads(response.json()['detail'])
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"{response_json['msg']} (HTTP_{response.status_code})"
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
    except KeyError:
        raise ServerError(
            f"An error has occurred with the response from the server with the "
            f"URL: {url}"
        )


def get_file(filepath: str, user: str = None, group: str = None):
    """Make a request to get a single file from the NLDS.
    :param filepath: the path of the file to get from the storage
    :type filepath: string
    :param user: the username to get the file
    :type user: string, optional
    :param group: the group to get the file
    :type group: string

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)

    # get an OAuth token and build the header with it in
    auth_token = load_or_fetch_oauth2_token(config, interactive = True)
    token_headers = {
        "Content-Type"  : "application/json",
        "cache-control" : "no-cache",
        "Authorization" : f"Bearer {auth_token['access_token']}"
    }

    url = construct_server_url(config)

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

    # make the request
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

    response_json = process_response(response, url)
    response_json = response.json()
    return response_json

def get_file_list(filelist: List[str] = [],
                  user: str = None, group: str = None):
    """Make a request to get a list of files from the NLDS.
    :param filelist: the list of filepaths to get from the storage
    :type filelist: List[string]

    :param user: the username to get the files
    :type user: string, optional

    :param group: the group to get the files
    :type group: string, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)

    # get an OAuth token and build the header with it in
    auth_token = load_or_fetch_oauth2_token(config, interactive = True)
    token_headers = {
        "Content-Type"  : "application/json",
        "cache-control" : "no-cache",
        "Authorization" : f"Bearer {auth_token['access_token']}"
    }

    url = construct_server_url(config) + "/getlist"

    # build the parameters.  files/getlist/put requires:
    #    transaction_id: UUID
    #    user: str
    #    group: str
    # and the filelist in the body

    # create the transaction ID
    transaction_id = uuid.uuid4()
    input_params = {"transaction_id" : transaction_id,
                    "user" : user,
                    "group" : group}
    body_params = {"filelist" : filelist}
    # make the request
    try:
        response = requests.put(
            url,
            headers = token_headers,
            params = input_params,
            json = body_params
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Could not connect to the URL: {url}\n"
            "Check the ['server']['url'] and ['server']['api'] setting in the "
            f"{CONFIG_FILE_LOCATION} file."
        )

    response = process_response(response, url)
    response_json = response.json()
    return response_json


def put_file(filepath: str, user: str = None, group: str = None):
    """Make a request to put a single file into the NLDS.

    :param filepath: the path of the file to put into the storage
    :type filepath: string

    :param user: the username to put the file
    :type user: string, optional

    :param group: the group to put the file
    :type group: string, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)

    # get an OAuth token and build the header with it in
    auth_token = load_or_fetch_oauth2_token(config, interactive = True)
    token_headers = {
        "Content-Type"  : "application/json",
        "cache-control" : "no-cache",
        "Authorization" : f"Bearer {auth_token['access_token']}"
    }

    url = construct_server_url(config)

    # build the parameters.  files/put requires:
    #    transaction_id: UUID
    #    user: str
    #    group: str
    #    filepath : str (optional)
    # create the transaction ID
    transaction_id = uuid.uuid4()
    input_params = {"transaction_id" : transaction_id,
                    "user" : user,
                    "group" : group,
                    "filepath" : filepath}

    # make the request
    try:
        response = requests.put(
            url,
            headers = token_headers,
            params = input_params,
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Could not connect to the URL: {url}\n"
            "Check the ['server']['url'] and ['server']['api'] setting in the "
            f"{CONFIG_FILE_LOCATION} file."
        )

    response = process_response(response, url)
    response_json = response.json()
    return response_json


def put_file_list(filelist: List[str] = [],
                  user: str = None, group: str = None):
    """Make a request to put a list of files into the NLDS.
    :param filelist: the list of filepaths to put into storage
    :type filelist: List[string]

    :param user: the username to put the files
    :type user: string

    :param group: the group to put the files
    :type group: string

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)

    # get an OAuth token and build the header with it in
    auth_token = load_or_fetch_oauth2_token(config, interactive = True)
    token_headers = {
        "Content-Type"  : "application/json",
        "cache-control" : "no-cache",
        "Authorization" : f"Bearer {auth_token['access_token']}"
    }

    url = construct_server_url(config)

    # build the parameters.  files/put requires:
    #    transaction_id: UUID
    #    user: str
    #    group: str
    # and the filelist in the body

    # create the transaction ID
    transaction_id = uuid.uuid4()
    input_params = {"transaction_id" : transaction_id,
                    "user" : user,
                    "group" : group}
    body_params = {"filelist" : filelist}
    # make the request
    try:
        response = requests.put(
            url,
            headers = token_headers,
            params = input_params,
            json = body_params
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Could not connect to the URL: {url}\n"
            "Check the ['server']['url'] and ['server']['api'] setting in the "
            f"{CONFIG_FILE_LOCATION} file."
        )

    response = process_response(response, url)
    response_json = response.json()
    return response_json
