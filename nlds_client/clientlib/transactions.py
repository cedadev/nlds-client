"""

"""

__author__ = "Neil Massey and Jack Leland"
__date__ = "29 Jan 2024"
__copyright__ = "Copyright 2024 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"
__contact__ = "neil.massey@stfc.ac.uk"

import json
import uuid
import urllib.parse
import os
from pathlib import Path
from datetime import datetime
from base64 import b64decode
from typing import List, Dict, Any

import requests

from nlds_client.clientlib.config import (
    load_config,
    create_config,
    write_auth_section,
    get_user,
    get_group,
    get_option,
    get_tenancy,
    get_access_key,
    get_secret_key,
)
from nlds_client.clientlib.authentication import (
    load_token,
    get_username_password,
    fetch_oauth2_token,
    fetch_oauth2_token_from_refresh,
)
from nlds_client.clientlib.exceptions import *

from nlds_client.clientlib.nlds_client_setup import (
    CONFIG_FILE_LOCATION,
    DEFAULT_SERVER_URL,
)


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
    url = (
        urllib.parse.urljoin(
            config["server"]["url"], "/".join([config["server"]["api"], method])
        )
    ) + "/"
    return url


def process_transaction_response(
    response: requests.models.Response, url: str, config: dict
):
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
        if (
            response.status_code == requests.codes.ok
            or response.status_code == requests.codes.accepted
        ):
            return response
        elif response.status_code == requests.codes.bad_request:  # 400 error
            response_json = json.loads(response.json()["detail"])
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"{response_json['msg']} (HTTP_{response.status_code})",
                response.status_code,
            )
        elif response.status_code == requests.codes.unauthorized:  # 401
            raise AuthenticationError(
                f"Could not complete the request to the URL: {url} \n"
                "Authentication failed.  Check that the token in the "
                f"{config['authentication']['oauth_token_file_location']} file "
                f"is a valid token (HTTP_{response.status_code})",
                response.status_code,
            )
        elif response.status_code == requests.codes.forbidden:  # 403
            raise AuthenticationError(
                f"Could not complete the request to the URL: {url} \n"
                "Authentication failed.  Check that the token in the "
                f"{config['authentication']['oauth_token_file_location']} file "
                f"is a valid token (HTTP_{response.status_code})",
                response.status_code,
            )
        elif response.status_code == requests.codes.not_found:  # 404
            response_msg = response.json()["detail"]
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"Response was: {response_msg} (HTTP_{response.status_code})",
                response.status_code,
            )
        elif response.status_code == requests.codes.unprocessable:  # 422
            response_msg = response.json()["detail"]
            raise RequestError(
                f"Could not complete the request to the URL: {url} \n"
                f"{response_msg} (HTTP_{response.status_code})",
                response.status_code,
            )
        else:
            raise RequestError(
                f"Could not complete the request to the URL: {url} "
                f"(HTTP_{response.status_code})",
                response.status_code,
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
        tag_str += key + ":" + tag[key] + ","
    tag_str = tag_str.replace("'", "")
    return tag_str[:-1]


def main_loop(
    url: str,
    input_params: Dict = None,
    body_params: Dict = None,
    authenticate_fl: bool = True,
    method=requests.get,
    **kwargs,
):
    """Generalised main loop to make requests to the NLDS server
    :param url: the API URL to contact
    :type user: string

    :param input_params: the input parameters for the API request (or None)
    :type input_params: dict

    :param body_params: the body parameters for the API request (or None)
    :type body_params: dict

    :raises requests.exceptions.ConnectionError: if the server cannot be
    reached

    :return: A Dictionary of the response or None
    :rtype: Dict
    """
    # Convert input parameters to empty dictionaries if None
    if input_params is None:
        input_params = {}
    if body_params is None:
        body_params = {}

    config = load_config()
    c_try = 0
    MAX_LOOPS = 2

    # Prioritise kwarg over config file value
    if "verify" in kwargs:
        verify = kwargs.pop("verify")
    else:
        verify = get_option(config, "verify_certificates")

    # If we're not verifying the certificate we can turn off the warnings about
    # it
    if not verify:
        from urllib3.connectionpool import InsecureRequestWarning
        import warnings

        warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    while c_try < MAX_LOOPS:
        c_try += 1
        token_headers = {
            "Content-Type": "application/json",
            "cache-control": "no-cache",
        }

        # Attempt to do authentication if flag set
        if authenticate_fl:
            try:
                auth_token = load_token(config)
            except FileNotFoundError:
                # we need the username and password to get the OAuth2 token in
                # the password flow
                username, password = get_username_password(config)
                auth_token = fetch_oauth2_token(config, username, password)
                # we don't want to do the rest of the loop!
                continue
            token_headers["Authorization"] = f"Bearer {auth_token['access_token']}"

        # make the request
        try:
            response = method(
                url,
                headers=token_headers,
                params=input_params,
                json=body_params,
                verify=verify,
                **kwargs,
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
                if (
                    ae.status_code == requests.codes.unauthorized
                    or ae.status_code == requests.codes.bad_request
                ):
                    os.remove(
                        os.path.expanduser(
                            config["authentication"]["oauth_token_file_location"]
                        )
                    )
                    continue
                else:
                    raise ae

        response_dict = json.loads(response.json())
        response_dict["success"] = True
        return response_dict

    # If we get to this point then the transaction could not be processed
    return None


def put_filelist(
    filelist: List[str] = [],
    user: str = None,
    group: str = None,
    job_label: str = None,
    label: str = None,
    holding_id: int = None,
    tag: Dict = None,
) -> Dict:
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
    # Convert tag parameter to empty dictionaries if None
    if tag is None:
        tag = {}

    # get the config, user and group
    config = load_config()
    user = get_user(config, user)
    group = get_group(config, group)
    url = construct_server_url(config, "files")
    tenancy = get_tenancy(config)
    access_key = get_access_key(config)
    secret_key = get_secret_key(config)
    transaction_id = uuid.uuid4()

    # Resolve the path to the file (i.e. make absolute)
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

    input_params = {
        "transaction_id": transaction_id,
        "user": user,
        "group": group,
        "access_key": access_key,
        "secret_key": secret_key,
        "tenancy": tenancy,
    }

    body_params = {"filelist": filelist}
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
        # tags in body params should not be encoded as a string
        body_params["tag"] = tag
    if holding_id is not None:
        body_params["holding_id"] = holding_id
    # make the request
    response_dict = main_loop(
        url=url, input_params=input_params, body_params=body_params, method=requests.put
    )

    if not response_dict:
        # If we get to this point then the transaction could not be processed
        response_dict = {
            "uuid": str(transaction_id),
            "msg": f"PUT transaction with id {transaction_id} failed",
            "success": False,
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def get_filelist(
    filelist: List[str] = [],
    user: str = None,
    group: str = None,
    groupall: bool = False,
    target: str = None,
    job_label: str = None,
    label: str = None,
    holding_id: int = None,
    tag: Dict = None,
) -> Dict:
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

    # If target given then we're downloading the file to a new location
    if target:
        target_p = Path(target)
        # Convert to a pathlib.Path to resolve and then back to a string
        target = str(target_p.resolve())
        # Recursively create the target path if it doesn't exist
        # NOTE: what permissions should be on this? Should _we_ be creating it
        # here? or should we just error at this point?
        if not target_p.exists():
            os.makedirs(target)
    # If no target given then we're downloading files back to their original locations.
    else:
        # Resolve path to file (i.e. make absolute)
        # Convert to a pathlib.Path to resolve, and then back to a string
        filelist = [str(Path(fp).resolve()) for fp in filelist]

    # if there is only one file then call "get" HTTP API method
    if len(filelist) == 1:
        # have to remove the extra ["/"] from the end of construct_server_url for get
        url = construct_server_url(config, f"files?filepath={filelist[0]}")[:-1]
        call_method = requests.get
    else:
        url = construct_server_url(config, "files/getlist")
        call_method = requests.put

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
    input_params = {
        "transaction_id": transaction_id,
        "user": user,
        "group": group,
        "groupall": groupall,
        "access_key": access_key,
        "secret_key": secret_key,
        "tenancy": tenancy,
        "target": target,
    }
    body_params = {"filelist": filelist}
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
        url=url, input_params=input_params, body_params=body_params, method=call_method
    )
    if not response_dict:
        # If we get to this point then the transaction could not be processed
        response_dict = {
            "uuid": str(transaction_id),
            "msg": f"GET transaction with id {transaction_id} failed",
            "success": False,
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def list_holding(
    user: str,
    group: str,
    groupall: bool = False,
    label: str = None,
    holding_id: int = None,
    transaction_id: str = None,
    tag: Dict = None,
):
    """Make a request to list the holdings in the NLDS for a user
    :param user: the username to get the holding(s) for
    :type user: string

    :param group: the group to get the holding(s) for
    :type group: string

    :param groupall: list holdings for the entire group, not just the user
    :type groupall: bool

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
    input_params = {"user": user, "group": group, "groupall": groupall}

    # add additional / optional components to input params
    if label is not None:
        input_params["label"] = label
    if tag is not None:
        input_params["tag"] = tag_to_string(tag)
    if holding_id is not None:
        input_params["holding_id"] = holding_id
    if transaction_id is not None:
        input_params["transaction_id"] = transaction_id

    response_dict = main_loop(url=url, input_params=input_params, method=requests.get)

    if not response_dict:
        response_dict = {
            "msg": f"LIST holdings for user {user} and group {group} failed",
            "success": False,
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def find_file(
    user: str,
    group: str,
    groupall: bool = False,
    label: str = None,
    holding_id: int = None,
    transaction_id: str = None,
    path: str = None,
    tag: Dict = None,
):
    """Make a request to find files in the NLDS for a user
    :param user: the username to get the holding(s) for
    :type user: string

    :param group: the group to get the holding(s) for
    :type group: string

    :param groupall: list files for the entire group, not just the user
    :type groupall: bool

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
    input_params = {"user": user, "group": group, "groupall": groupall}

    # add additional / optional components to input params
    if label is not None:
        input_params["label"] = label
    if tag is not None:
        input_params["tag"] = tag_to_string(tag)
    if holding_id is not None:
        input_params["holding_id"] = holding_id
    if transaction_id is not None:
        input_params["transaction_id"] = transaction_id
    if path is not None:
        input_params["path"] = path

    response_dict = main_loop(url=url, input_params=input_params, method=requests.get)

    if not response_dict:
        response_dict = {
            "msg": f"FIND files for user {user} and group {group} failed",
            "success": False,
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def monitor_transactions(
    user: str,
    group: str,
    groupall: bool = False,
    idd: int = None,
    transaction_id: str = None,
    job_label: str = None,
    api_action: str = None,
    state: str = None,
    sub_id: str = None,
):
    """Make a request to the monitoring database for a status update of ongoing
    or finished transactions in the NLDS for, a user/group

    :param user: the username to get the transaction state(s) for
    :type user: string

    :param group: the group to get the transaction state(s) for
    :type group: string

    :param groupall: list transactions for the entire group, not just the user
    :type groupall: bool

    :param idd: the numeric id (primary key) of the transaction
    :type idd: int

    :param transaction_id: a specific transaction_id to get the status of
    :type transaction_id: string, optional

    :param job_label: a specific job_label to get the status of
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
    input_params = {"user": user, "group": group, "groupall": groupall}

    # add additional / optional components to input params
    if idd is not None:
        input_params["id"] = idd
    if transaction_id is not None:
        input_params["transaction_id"] = transaction_id
    if job_label is not None:
        input_params["job_label"] = job_label
    if api_action is not None:
        input_params["api_action"] = api_action
    if sub_id is not None:
        input_params["sub_id"] = sub_id
    if state is not None:
        input_params["state"] = state

    response_dict = main_loop(url=url, input_params=input_params, method=requests.get)

    # If we get to this point then the transaction could not be processed
    if not response_dict:
        response_dict = {
            "msg": f"STAT transaction for user {user} and group {group} failed",
            "success": False,
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False

    return response_dict


def get_transaction_state(transaction: dict):
    """Get the overall state of a transaction in a more convienent form by
    querying the sub-transactions and determining if the overall transaction
    is complete.
    transaction: a dictionary for a single transaction.  Note that
      monitor_transactions returns a dictionary of transactions
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
            CATALOG_PUTTING = 3
            TRANSFER_PUTTING = 4
            CATALOG_ROLLBACK = 5
            CATALOG_GETTING = 10
            ARCHIVE_GETTING = 11
            TRANSFER_GETTING = 12
            ARCHIVE_INIT = 20
            CATALOG_ARCHIVE_AGGREGATING = 21
            ARCHIVE_PUTTING = 22
            CATALOG_ARCHIVE_UPDATING = 23
            CATALOG_ARCHIVE_ROLLBACK = 40
            COMPLETE = 100
            FAILED = 101
            COMPLETE_WITH_ERRORS = 102
            COMPLETE_WITH_WARNINGS = 103
    The overall state is the minimum of these
    """
    state_mapping = {
        "INITIALISING": -1,
        "ROUTING": 0,
        "SPLITTING": 1,
        "INDEXING": 2,
        "CATALOG_PUTTING": 3,
        "TRANSFER_PUTTING": 4,
        "CATALOG_ROLLBACK": 5,
        "CATALOG_UPDATING": 6,
        "CATALOG_GETTING": 10,
        "ARCHIVE_GETTING": 11,
        "TRANSFER_GETTING": 12,
        "ARCHIVE_INIT": 20,
        "CATALOG_ARCHIVE_AGGREGATING": 21,
        "ARCHIVE_PUTTING": 22,
        "CATALOG_ARCHIVE_UPDATING": 23,
        "CATALOG_ARCHIVE_REMOVING": 40,
        "CATALOG_DELETE_ROLLBACK": 41,
        "CATALOG_RESTORING": 42,
        "COMPLETE": 100,
        "FAILED": 101,
        "COMPLETE_WITH_ERRORS": 102,
        "COMPLETE_WITH_WARNINGS": 103,
    }
    state_mapping_reverse = {v: k for k, v in state_mapping.items()}

    min_state = 200
    min_time = datetime(1970, 1, 1)
    error_count = 0
    for sr in transaction["sub_records"]:
        sr_state = sr["state"]
        d = datetime.fromisoformat(sr["last_updated"])
        if d > min_time:
            min_time = d
        if state_mapping[sr_state] < min_state:
            min_state = state_mapping[sr_state]
        if sr_state == "FAILED":
            error_count += 1

    if min_state == 200:
        return None, None

    if min_state == state_mapping["COMPLETE"] and error_count > 0:
        min_state = state_mapping["COMPLETE_WITH_ERRORS"]

    # see if any warnings were given
    warning_count = 0
    if "warnings" in transaction:
        warning_count = len(transaction["warnings"])
    if min_state == state_mapping["COMPLETE"] and warning_count > 0:
        min_state = state_mapping["COMPLETE_WITH_WARNINGS"]

    return state_mapping_reverse[min_state], min_time


def change_metadata(
    user: str,
    group: str,
    label: str = None,
    holding_id: int = None,
    tag: Dict = None,
    new_label: str = None,
    new_tag: Dict = None,
    del_tag: Dict = None,
):
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

    :param new_tag: the tag(s) to add / change for the holding
    :type new_tag: dict, optional

    :param del_tag: the tag(s) to delete for the holding
    :type del_tag: dict, optional

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
    input_params = {"user": user, "group": group}
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
    if del_tag is not None:
        body_params["del_tag"] = del_tag

    response_dict = main_loop(
        url=url,
        input_params=input_params,
        body_params=body_params,
        method=requests.post,  # post method as we are changing a resource
    )

    if not response_dict:
        response_dict = {
            "msg": f"FIND files for user {user} and group {group} failed",
            "success": False,
        }
    # mark as failed in RPC call
    elif "details" in response_dict and "failure" in response_dict["details"]:
        response_dict["success"] = False
    return response_dict


def init_client(
    url: str = None,
    verify_certificates: bool = True,
) -> Dict[str, Any]:
    """Make two requests to the API to get some secret, encrypted configuration
    information and then the token to help decrypt it.

    :param url: The url to request initiation details from. Must start with
                'http://' or 'https://'.
    :type url:  str, optional

    :param verify_certificates: Boolean flag controlling whether to verify ssl
                                certificates during the get request.
    :type verify_certificates:  bool, optional

    :return: A dict containing information about the outcome of the initiation,
             i.e. whether it succeeded and whether a file was created.
    :rtype: Dict
    """
    from cryptography.fernet import Fernet

    # Use the default NLDS url if none provided
    if url is None:
        url = DEFAULT_SERVER_URL
    cli_response = {"success": True, "new_config": False}

    try:
        # get the config, if it exists, and change the url to that provided
        config = load_config()
        config["server"]["url"] = url
    except FileNotFoundError:
        # If the file doesn't exist then create it
        config = create_config(url, verify_certificates)
        cli_response["new_config"] = True

    responses = {}
    for endpoint in ["init", "init/token"]:
        url = construct_server_url(config, endpoint)
        response_dict = main_loop(
            url=url,
            input_params=None,
            method=requests.get,
            allow_redirects=True,
            verify=verify_certificates,
            authenticate_fl=False,
        )

        # If we get to this point then the transaction could not be processed
        if not response_dict:
            raise RequestError(f"Could not init NLDS, empty response")
        responses[endpoint] = response_dict

    try:
        key = b64decode(responses["init/token"]["token"])
        auth_config_enc = responses["init"]["encrypted_keys"]
    except (KeyError, AttributeError) as e:
        raise RequestError(
            "Malformed init response from api, could not create "
            f"config file {type(e).__name__}:{e}",
            requests.codes.unprocessable,
        )

    # Decrypt the encrypted keys
    f = Fernet(key)
    auth_config = json.loads(f.decrypt(auth_config_enc))

    # Write auth_config to config file
    write_auth_section(config, auth_config)

    return cli_response
