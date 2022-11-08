import requests
import json
import uuid
import urllib.parse
import os
from pathlib import Path

from typing import List, Dict

from nlds_client.clientlib.config import load_config, get_user, get_group, \
                            get_option, \
                            get_tenancy, get_access_key, get_secret_key
from nlds_client.clientlib.authentication import load_token,\
                                     get_username_password,\
                                     fetch_oauth2_token,\
                                     fetch_oauth2_token_from_refresh
from nlds_client.clientlib.exceptions import *

from nlds_client.clientlib.nlds_client_setup import CONFIG_FILE_LOCATION


def construct_server_url(config: Dict, method=""):
    """Construct the url from the details in the config file.
    :param config: dictionary of key:value pairs returned from the load_config
    function.
    :type config: Dict

    :param method: API method to call, currently either "files" or "holdings"
    :type method: string

    :return: a fully qualified url to the server hosting the REST API for NLDS.
    :rtype: string
    """
    url = urllib.parse.urljoin(config["server"]["url"],
                               "/".join([config["server"]["api"],
                               method])
                              ) + "/"
    return url


def process_transaction_response(response: requests.models.Response, url: str,
                                 config: Dict):
    """Process the response to raise exceptions for errors or return the
    response result.

    :param response: response from the requests method (put, get, post, delete
    etc.)
    :type response: requests.models.Response

    :param url: the url from the construct_server_url function, required
    to format error messages
    :type url: string

    :param config: the configuration Dictionary loaded by config.load_config]
    :type config: Dict

    :raises RequestError: the request to the REST API is ill-formed
    :raises AuthenticationError: the user is not authorised to access the REST
    API or the data they are trying to access
    :raises ServerError: something is wrong with the server

    :return: A requests response object, if none of the exceptions are
    triggered.
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
                f"{response_json['msg']} (HTTP_{response.status_code})",
                response.status_code
            )
        elif (response.status_code == requests.codes.unauthorized): # 401
            raise AuthenticationError(
                f"Could not complete the request to the URL: {url} \n"
                "Authentication failed.  Check that the token in the "
                f"{config['authentication']['oauth_token_file_location']} file "
                f"is a valid token (HTTP_{response.status_code})",
                response.status_code
            )
        elif (response.status_code == requests.codes.forbidden):   # 403
            raise AuthenticationError(
                f"Could not complete the request to the URL: {url} \n"
                "Authentication failed.  Check that the token in the "
                f"{config['authentication']['oauth_token_file_location']} file "
                f"is a valid token (HTTP_{response.status_code})",
                response.status_code
            )
        elif (response.status_code == requests.codes.not_found):   # 404
            response_json = json.loads(response.json()['detail'])
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"{response_json['msg']} (HTTP_{response.status_code})",
                response.status_code
            )
        elif (response.status_code == requests.codes.unprocessable): # 422
            response_json = response.json()['detail'][0]
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"{response_json['msg']} (HTTP_{response.status_code})",
                response.status_code
            )
        else:
            raise RequestError(
                f"Could not complete the request to the URL: {url} "
                f"(HTTP_{response.status_code})",
                response.status_code
            )
    except KeyError:
        raise ServerError(
            f"An error has occurred with the response from the server with the "
            f"URL: {url}"
        )


def get_filelist(filelist: List[str]=[],
                 user: str=None, group: str=None, target: str = None,
                 label: str=None, holding_id: int=None, tag: dict=None) -> Dict:
    """Make a request to get a list of files from the NLDS.
    :param filelist: the list of filepaths to get from the storage
    :type filelist: List[string]

    :param user: the username to get the files
    :type user: string, optional

    :param group: the group to get the files
    :type group: string, optional

    :param target: the location to write the retrieved files to
    :type target: string, optional

    :param label: the label of an existing holding that files are to be 
    retrieved from
    :type label: str, optional

    :param holding_id: the integer id of a holding that files are to be 
    retrieved from
    :type holding_id: int, optional

    :param tag: a dictionary of key:value pairs to search for in a holding that 
    files are to be retrieved from
    :type tag: dict, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    # try 3 times:
    #   1. With token loaded from file at config["oauth_token_file_location"]
    #   2. With a refresh token
    #   3. Delete the token file

    c_try = 0
    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    tenancy = get_tenancy(config)
    access_key = get_access_key(config)
    secret_key = get_secret_key(config)
    transaction_id = uuid.uuid4()
    url = construct_server_url(config, "files") + "getlist"
    MAX_LOOPS = 2

    # If target given then we're operating in "mode 2" where we're downloading 
    # the file to a new location
    if target:
        target_p = Path(target)
        # Resolve path to target (i.e. make absolute) if configured so
        if get_option(config, "resolve_filenames"):
            # Convert to a pathlib.Path to resolve and then back to a string
            target = str(target_p.resolve())
        # Recursively create the target path if it doesn't exist
        # NOTE: what permissions should be on this? Should _we_ be creating it
        # here? or should we just error at this point?
        if not target_p.exists():
            os.makedirs(target)
    # If no target given then we are operating in "mode 1", i.e. we're 
    # downloading files back to their original locations.
    else:
        # Resolve path to file (i.e. make absolute) if configured so
        if get_option(config, "resolve_filenames"):
            # Convert to a pathlib.Path to resolve, and then back to a string
            filelist = [str(Path(fp).resolve()) for fp in filelist]

    while c_try < MAX_LOOPS:
        # get an OAuth token if we fail then the file doesn't exist.
        # we then fetch an Oauth2 token and try again
        c_try += 1
        try:
            auth_token = load_token(config)
        except FileNotFoundError:
            # we need the username and password to get the OAuth2 token in
            # the password flow
            username, password = get_username_password(config)
            auth_token = fetch_oauth2_token(config, username, password)
            # we don't want to do the rest of the loop!
            continue

        token_headers = {
            "Content-Type"  : "application/json",
            "cache-control" : "no-cache",
            "Authorization" : f"Bearer {auth_token['access_token']}"
        }

        # build the parameters.  files/getlist/put requires:
        #    transaction_id     : UUID
        #    user               : str
        #    group              : str
        #    access_key         : str
        #    secret_key         : str
        #    tenancy            : str (optional)
        #    target             : str (optional - defaults to cwd)
        # and the filelist in the body
        input_params = {"transaction_id" : transaction_id,
                        "user" : user,
                        "group" : group,
                        "access_key" : access_key,
                        "secret_key" : secret_key,
                        "tenancy" : tenancy,
                        "target": target,
                    }
        body_params = {"filelist" : filelist}
        # add optional components to body: label, tags, holding_id
        if label is not None:
            body_params["label"] = label
        if tag is not None:
            body_params["tag"] = tag
        if holding_id is not None:
            body_params["holding_id"] = holding_id
        # make the request
        try:
            response = requests.put(
                url,
                headers = token_headers,
                params = input_params,
                json = body_params,
                verify = get_option(config, 'verify_certificates')
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to the URL: {url}\n"
                "Check the ['server']['url'] and ['server']['api'] setting in "
                f"the {CONFIG_FILE_LOCATION} file."
            )

        # process the returned response
        try:
            process_transaction_response(response, url, config)
        except AuthenticationError:
            # try to get a new token via the refresh method
            try:
                auth_token = fetch_oauth2_token_from_refresh(config)
                continue
            except (AuthenticationError, RequestError) as ae:
                # delete the token file ready to try again!
                if (ae.status_code == requests.codes.unauthorized or
                    ae.status_code == requests.codes.bad_request):
                    os.remove(os.path.expanduser(
                        config['authentication']['oauth_token_file_location']
                    ))
                    continue
                else:
                    raise ae

        response_dict = json.loads(response.json())
        response_dict['success'] = True
        return response_dict

    # If we get to this point then the transaction could not be processed
    response_dict = {'uuid' : str(transaction_id),
                     'msg'  : f'GETLIST transaction with id {transaction_id} failed',
                     'success' : False
                    }
    return response_dict


def put_filelist(filelist: List[str]=[],
                 user: str=None, group: str=None,
                 label: str=None, holding_id: int=None, tag: dict=None):
    """Make a request to put a list of files into the NLDS.
    :param filelist: the list of filepaths to put into storage
    :type filelist: List[string]

    :param user: the username to put the files
    :type user: string

    :param group: the group to put the files
    :type group: string

    :param label: the label of an existing holding that files are to be added to
    :type label: str, optional

    :param holding_id: the integer id of an existing holding that files are to be added to
    :type holding_id: int, optional

    :param tag: a dictionary of key:value pairs to add as tags to the holding upon creation
    :type tag: dict, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    c_try = 0
    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    tenancy = get_tenancy(config)
    access_key = get_access_key(config)
    secret_key = get_secret_key(config)
    transaction_id = uuid.uuid4()
    url = construct_server_url(config, "files")
    MAX_LOOPS = 2
    
    # Resolve path to file (i.e. make absolute) if configured so
    if get_option(config, "resolve_filenames"):
        # Convert to a pathlib.Path and then back to a string
        filelist = [str(Path(fp).resolve()) for fp in filelist]

    while c_try < MAX_LOOPS:

        # get an OAuth token if we fail then the file doesn't exist.
        # we then fetch an Oauth2 token and try again
        c_try += 1
        try:
            auth_token = load_token(config)
        except FileNotFoundError:
            # we need the username and password to get the OAuth2 token in
            # the password flow
            username, password = get_username_password(config)
            auth_token = fetch_oauth2_token(config, username, password)
            # we don't want to do the rest of the loop!
            continue

        token_headers = {
            "Content-Type"  : "application/json",
            "cache-control" : "no-cache",
            "Authorization" : f"Bearer {auth_token['access_token']}"
        }

        # build the parameters.  files/put requires (for a filelist):
        #    transaction_id: UUID
        #    user: str
        #    group: str
        #    access_key: str
        #    secret_key: str
        #    tenancy: str (optional)
        # and the filelist in the body

        input_params = {"transaction_id" : transaction_id,
                        "user" : user,
                        "group" : group,
                        "access_key" : access_key,
                        "secret_key" : secret_key,
                        "tenancy" : tenancy
                    }
        body_params = {"filelist" : filelist}
        # add optional components to body: label, tags, holding_id
        if label is not None:
            body_params["label"] = label
        if tag is not None:
            body_params["tag"] = tag
        if holding_id is not None:
            body_params["holding_id"] = holding_id
        # make the request
        try:
            response = requests.put(
                url,
                headers = token_headers,
                params = input_params,
                json = body_params,
                verify = get_option(config, 'verify_certificates')
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to the URL: {url}\n"
                "Check the ['server']['url'] and ['server']['api'] setting in "
                f"the {CONFIG_FILE_LOCATION} file."
            )

        # process the returned response
        try:
            process_transaction_response(response, url, config)
        except AuthenticationError:
            # try to get a new token via the refresh method
            try:
                auth_token = fetch_oauth2_token_from_refresh(config)
                continue
            except (AuthenticationError, RequestError) as ae:
                # delete the token file ready to try again!
                if (ae.status_code == requests.codes.unauthorized or
                    ae.status_code == requests.codes.bad_request):
                    os.remove(os.path.expanduser(
                        config['authentication']['oauth_token_file_location']
                    ))
                    continue
                else:
                    raise ae

        response_dict = json.loads(response.json())
        response_dict['success'] = True
        return response_dict

    # If we get to this point then the transaction could not be processed
    response_dict = {'uuid' : str(transaction_id),
                     'msg'  : f'PUT transaction with id {transaction_id} failed',
                     'success' : False
                    }
    return response_dict


def list_holding(user: str, group: str, 
                 label: str, holding_id: int, tag: dict):
    """Make a request to list the holdings in the NLDS for a user
    :param user: the username to get the holding(s) for
    :type user: string

    :param group: the group to get the holding(s) for
    :type group: string

    :param label: the label of an existing holding to get the details for
    :type label: str, optional

    :param holding_id: the integer id of an existing holding to get the details
    :type holding_id: int, optional

    :param tag: a list of key:value pairs to search holdings for - return
        holdings with these tags.  This will be converted to dictionary before 
        calling the remote method.
    :type tag: dict, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    c_try = 0
    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    tenancy = get_tenancy(config)
    access_key = get_access_key(config)
    secret_key = get_secret_key(config)
    transaction_id = uuid.uuid4()
    url = construct_server_url(config, "holdings")
    MAX_LOOPS = 2
    
    while c_try < MAX_LOOPS:
        c_try += 1
        try:
            auth_token = load_token(config)
        except FileNotFoundError:
            # we need the username and password to get the OAuth2 token in
            # the password flow
            username, password = get_username_password(config)
            auth_token = fetch_oauth2_token(config, username, password)
            # we don't want to do the rest of the loop!
            continue

        token_headers = {
            "Content-Type"  : "application/json",
            "cache-control" : "no-cache",
            "Authorization" : f"Bearer {auth_token['access_token']}"
        }

        # build the parameters.  holdings->get requires
        #    user: str
        #    group: str
        input_params = {"user" : user,
                        "group" : group}

        # add additional / optional components to input params
        if label is not None:
            input_params["label"] = label
        if tag is not None:
            # convert dict to string
            tag_str = ""
            for key in tag:
                tag_str += key+":"+tag[key]+","
            input_params["tag"] = str(tag).replace("'","")
        if holding_id is not None:
            input_params["holding_id"] = holding_id

        # make the request
        try:
            response = requests.get(
                url,
                headers = token_headers,
                params = input_params,
                verify = get_option(config, 'verify_certificates')
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to the URL: {url}\n"
                "Check the ['server']['url'] and ['server']['api'] setting in "
                f"the {CONFIG_FILE_LOCATION} file."
            )
        # process the returned response
        try:
            process_transaction_response(response, url, config)
        except AuthenticationError:
            # try to get a new token via the refresh method
            try:
                auth_token = fetch_oauth2_token_from_refresh(config)
                continue
            except (AuthenticationError, RequestError) as ae:
                # delete the token file ready to try again!
                if (ae.status_code == requests.codes.unauthorized or
                    ae.status_code == requests.codes.bad_request):
                    os.remove(os.path.expanduser(
                        config['authentication']['oauth_token_file_location']
                    ))
                    continue
                else:
                    raise ae

        response_dict = json.loads(response.json())
        response_dict['success'] = True
        return response_dict

    # If we get to this point then the transaction could not be processed
    response_dict = {'uuid' : str(transaction_id),
                     'msg'  : f'PUT transaction with id {transaction_id} failed',
                     'success' : False
                    }
    return response_dict