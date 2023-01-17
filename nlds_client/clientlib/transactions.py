import requests
import json
import uuid
import urllib.parse
import os
from pathlib import Path
from datetime import datetime

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


def process_transaction_response(response: requests.models.Response, 
                                 url: str,
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
            response_msg = response.json()['detail']
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"{response_msg} (HTTP_{response.status_code})",
                response.status_code
            )
        elif (response.status_code == requests.codes.unprocessable): # 422
            response_msg = response.json()['detail']
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"{response_msg} (HTTP_{response.status_code})",
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


def tag_to_string(tag: dict):
    """Convert a dictionary of tags into comma delimited string of key:value 
    pairs."""
    # convert dict to string
    tag_str = ""
    for key in tag:
        tag_str += key+":"+tag[key]+","
    tag_str = tag_str.replace("'","")
    return tag_str
    

def main_loop(url: str, 
              input_params: dict={}, 
              body_params: dict={},
              method=requests.get):
    """Generalised main loop to make requests to the NLDS server
    :param url: the API URL to contact
    :type user: string

    :param input_params: the input parameters for the API request (or {})
    :type input_params: dict

    :param body_params: the body parameters for the API request (or {})
    :type body_params: dict

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response or None
    :rtype: Dict
    """

    config = load_config()    
    c_try = 0
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

        # make the request
        try:
            response = method(
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
    return None


def put_filelist(filelist: List[str]=[],
                 user: str=None, 
                 group: str=None,
                 job_label: str=None,
                 label: str=None, 
                 holding_id: int=None, 
                 tag: dict=None):
    """Make a request to put a list of files into the NLDS.
    :param filelist: the list of filepaths to put into storage
    :type filelist: List[string]

    :param user: the username to put the files
    :type user: string

    :param group: the group to put the files
    :type group: string

    :param job_label: an optional label for the transaction to aid user queries
    :type job_label: string, optional

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

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    url = construct_server_url(config, "files")
    tenancy = get_tenancy(config)
    access_key = get_access_key(config)
    secret_key = get_secret_key(config)
    transaction_id = uuid.uuid4()

    # Resolve path to file (i.e. make absolute) if configured so
    if get_option(config, "resolve_filenames"):
        # Convert to a pathlib.Path and then back to a string
        filelist = [str(Path(fp).resolve()) for fp in filelist]

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
    # add optional job_label.  If None then use first 8 characters of UUID
    if job_label is None:
        if label is None:
            input_params["job_label"] = str(transaction_id)[0:8]
        else:
            input_params["job_label"] = label
    else:
        input_params["job_label"] = job_label
    # add optional components to body: label, tags, holding_id
    if label is not None:
        body_params["label"] = label
    if tag is not None:
        body_params["tag"] = tag_to_string(tag)
    if holding_id is not None:
        body_params["holding_id"] = holding_id
    # make the request
    response_dict = main_loop(
        url=url,
        input_params=input_params,
        body_params=body_params,
        method=requests.put
    )

    if not response_dict:
        # If we get to this point then the transaction could not be processed
        response_dict = {
            'uuid' : str(transaction_id),
            'msg'  : f'PUT transaction with id {transaction_id} failed',
            'success' : False
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def get_filelist(filelist: List[str]=[],
                 user: str=None, 
                 group: str=None, 
                 target: str = None,
                 job_label: str = None,
                 label: str=None, 
                 holding_id: int=None, 
                 tag: dict=None) -> Dict:
    """Make a request to get a list of files from the NLDS.
    :param filelist: the list of filepaths to get from the storage
    :type filelist: List[string]

    :param user: the username to get the files
    :type user: string, optional

    :param group: the group to get the files
    :type group: string, optional

    :param target: the location to write the retrieved files to
    :type target: string, optional

    :param job_label: an optional label for the transaction to aid user queries
    :type job_label: string, optional

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

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    tenancy = get_tenancy(config)
    access_key = get_access_key(config)
    secret_key = get_secret_key(config)
    transaction_id = uuid.uuid4()
    url = construct_server_url(config, "files") + "getlist"

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

    # build the parameters.  files/getlist/put requires:
    #    transaction_id     : UUID
    #    user               : str
    #    group              : str
    #    access_key         : str
    #    secret_key         : str
    #    tenancy            : str (optional)
    #    job_label          : str (optional)
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
    # add optional job_label.  If None then use first 8 characters of UUID
    if job_label is None:
        if label is None:
            input_params["job_label"] = str(transaction_id)[0:8]
        else:
            input_params["job_label"] = label
    else:
        input_params["job_label"] = job_label
    # add optional components to body: label, tags, holding_id
    if label is not None:
        body_params["label"] = label
    if tag is not None:
        body_params["tag"] = tag_to_string(tag)
    if holding_id is not None:
        body_params["holding_id"] = holding_id
    # make the request
    response_dict = main_loop(
        url=url,
        input_params=input_params,
        body_params=body_params,
        method=requests.put
    )
    if not response_dict:
        # If we get to this point then the transaction could not be processed
        response_dict = {
            "uuid" : str(transaction_id),
            "msg"  : f"GET transaction with id {transaction_id} failed",
            "success" : False
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def list_holding(user: str, 
                 group: str, 
                 label: str=None, 
                 holding_id: int=None, 
                 tag: dict=None):
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

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    url = construct_server_url(config, "catalog/list")

    # build the parameters.  holdings->get requires
    #    user: str
    #    group: str
    input_params = {"user" : user,
                    "group" : group}

    # add additional / optional components to input params
    if label is not None:
        input_params["label"] = label
    if tag is not None:
        input_params["tag"] = tag_to_string(tag)
    if holding_id is not None:
        input_params["holding_id"] = holding_id

    response_dict = main_loop(
        url=url, 
        input_params=input_params,
        method=requests.get
    )

    if not response_dict:
        response_dict = {
            "msg"  : f"LIST holdings for user {user} and group {group} failed",
            "success" : False
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def find_file(user: str, 
              group: str, 
              label: str=None, 
              holding_id: int=None,
              path: str=None,
              tag: dict=None):
    """Make a request to find files in the NLDS for a user
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

    :param path: path to search for, can be a substring, regex or wildcard
    :type path: str, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """
    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    url = construct_server_url(config, "catalog/find")

    # build the parameters.  holdings->get requires
    #    user: str
    #    group: str
    input_params = {"user" : user,
                    "group" : group}

    # add additional / optional components to input params
    if label is not None:
        input_params["label"] = label
    if tag is not None:
        input_params["tag"] = tag_to_string(tag)
    if holding_id is not None:
        input_params["holding_id"] = holding_id
    if path is not None:
        input_params["path"] = path

    response_dict = main_loop(
        url=url, 
        input_params=input_params,
        method=requests.get
    )

    if not response_dict:
        response_dict = {
            "msg"  : f"FIND files for user {user} and group {group} failed",
            "success" : False
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict    


def monitor_transactions(user: str, 
                         group: str, 
                         idd: int=None,
                         transaction_id: str=None, 
                         api_action: str=None,
                         state: str=None, 
                         sub_id: str=None,
                         retry_count: int=None):
    """Make a request to the monitoring database for a status update of ongoing 
    or finished transactions in the NLDS for, a user/group

    :param user: the username to get the transaction state(s) for
    :type user: string

    :param group: the group to get the transaction state(s) for
    :type group: string

    :param idd: the numeric id (primary key) of the transaction
    :type idd: int

    :param transaction_id: a specific transaction_id to get the status of 
    :type transaction_id: string, optional

    :param api_action: applies an api-action-specific filter to the status 
        request, only transaction_records of the given api_action will be 
        returned. 
    :type api_action: string, optional
    
    :param sub_id: a specific sub_id (of a sub_record) to get the status of 
    :type sub_id: string, optional

    :param state: applies a state-specific filter to the status request, only 
        sub_records at the given state will be returned.
    :type state: string, optional

    :param retry_count: returns sub_records at the given retry_count value
    :type retry_count: int, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    url = construct_server_url(config, "status")
    MAX_LOOPS = 2

    # build the parameters.  monitoring->get requires
    #    user: str
    #    group: str
    input_params = {"user" : user,
                    "group" : group}

    # add additional / optional components to input params
    if idd is not None:
        input_params["id"] = idd
    if transaction_id is not None:
        input_params["transaction_id"] = transaction_id
    if api_action is not None:
        input_params["api_action"] = api_action
    if sub_id is not None:
        input_params["sub_id"] = sub_id
    if state is not None:
        input_params["state"] = state
    if retry_count is not None:
        input_params["retry_count"] = retry_count

    response_dict = main_loop(
        url=url,
        input_params=input_params,
        method=requests.get
    )

    # If we get to this point then the transaction could not be processed
    if not response_dict:
        response_dict = {
            "msg": f"STAT transaction for user {user} and group {group} failed",
            "success": False
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def get_transaction_state(transaction: dict):
    """Get the overall state of a transaction in a more convienent form by 
    querying the sub-transactions and determining if the overall transaction 
    is complete.
    Transaction dictionary looks like this:
    {
        'id': 2, 
        'transaction_id': 'a06ec7b3-e83c-4ac7-97d8-2545a0b8d317', 
        'user': 'nrmassey', 
        'group': 'cedaproc', 
        'api_action': 'getlist', 
        'creation_time': '2022-12-06T15:45:43', 
        'sub_records': [
            {
                'id': 2, 
                'sub_id': '007075b2-8c79-4cfa-a1e5-0aaa65892454', 
                'state': 'COMPLETE', 
                'retry_count': 0, 
                'last_updated': '2022-12-06T15:45:44', 
                'failed_files': []
            }
        ]
    }

    possible values of state are: 
        INITIALISING = -1
        ROUTING = 0
        SPLITTING = 1
        INDEXING = 2
        TRANSFER_PUTTING = 3
        CATALOG_PUTTING = 4
        CATALOG_GETTING = 5
        TRANSFER_GETTING = 6
        COMPLETE = 8
        FAILED = 9
    The overall state is the minimum of these
    """
    state_mapping = {
        "INITIALISING" : -1,
        "ROUTING" : 0,
        "SPLITTING" : 1,
        "INDEXING" : 2,
        "TRANSFER_PUTTING" : 3,
        "CATALOG_PUTTING" : 4,
        "CATALOG_GETTING" : 5,
        "TRANSFER_GETTING" : 6,
        "COMPLETE" : 8,
        "FAILED" : 9,
    }
    state_mapping_reverse = {
        -1 : "INITIALISING",
        0 : "ROUTING",
        1 : "SPLITTING",
        2 : "INDEXING",
        3 : "TRANSFER_PUTTING" ,
        4 : "CATALOG_PUTTING",
        5 : "CATALOG_GETTING",
        6 : "TRANSFER_GETTING",
        8 : "COMPLETE",
        9 : "FAILED",
    }

    min_state = 100
    min_time = datetime(1970,1,1)
    for sr in transaction["sub_records"]:
        sr_state = sr["state"]
        d = datetime.fromisoformat(sr["last_updated"])
        if(d > min_time):
            min_time = d
        if state_mapping[sr_state] < min_state:
            min_state = state_mapping[sr_state]

    if min_state == 100:
        return None, None

    return state_mapping_reverse[min_state], min_time


def change_metadata(user: str, 
                    group: str, 
                    label: str=None, 
                    holding_id: int=None,
                    tag: dict=None,
                    new_label: str=None,
                    new_tag: dict=None):
    """Make a request to change the metadata for a NLDS holding for a user
    :param user: the username to change the holding(s) for
    :type user: string

    :param group: the group to change the holding(s) for
    :type group: string

    :param label: the label of an existing holding to change the details for
    :type label: str, optional

    :param holding_id: the integer id of an existing holding to change the details
    :type holding_id: int, optional

    :param tag: a list of key:value pairs to search holdings for - return
        holdings with these tags.  This will be converted to dictionary before 
        calling the remote method.
    :type tag: dict, optional

    :param new_label: the new label to change the label to for the holding
    :type new_label: str, optional

    :param new_tag: the tag to add / change for the holding
    :type new_tag: dict, optional

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response
    :rtype: Dict
    """
    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    url = construct_server_url(config, "catalog/meta")

    # build the parameters.  holdings->get requires
    #    user: str
    #    group: str
    input_params = {"user" : user,
                    "group" : group}
    body_params = {}
    # add additional / optional components to input params
    if label is not None:
        input_params["label"] = label
    if tag is not None:
        input_params["tag"] = tag_to_string(tag)
    if holding_id is not None:
        input_params["holding_id"] = holding_id
    # new metadata to amend / overwrite / add
    if new_label is not None:
        body_params["new_label"] = new_label
    if new_tag is not None:
        body_params["new_tag"] = new_tag

    response_dict = main_loop(
        url=url, 
        input_params=input_params,
        body_params=body_params,
        method=requests.post        # post method as we are changing a resource
    )

    if not response_dict:
        response_dict = {
            "msg"  : f"FIND files for user {user} and group {group} failed",
            "success" : False
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False
    return response_dict   