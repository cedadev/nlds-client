#! /usr/bin/env python
import click
from nlds_client.clientlib.transactions import (get_filelist, put_filelist,
                                                list_holding, find_file,
                                                monitor_transactions)
from nlds_client.clientlib.exceptions import ConnectionError, RequestError, \
                                             AuthenticationError
from nlds_client.clientlib.config import get_user, get_group, load_config

@click.group()
def nlds_client():
    pass


"""Custom class for tags in the format key:value 
(i.e. using the colon as separator between key and value."""

class TagParamType(click.ParamType):
    name = "tag"
    tag_dict = {}

    def convert(self, value, param, ctx):
        try:
            substrs = value.replace(" ","").split(",")
            for s in substrs:
                k, v = s.split(":")
                self.tag_dict[k] = v
        except ValueError:
            self.fail(
                f"{value!r} is not a valid (list of) tag(s)", param, ctx
            )
        return self.tag_dict

TAG_PARAM_TYPE = TagParamType()


"""Put files command"""
@nlds_client.command("put")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
@click.argument("filepath", type=str)
def put(filepath, user, group, label, holding_id, tag):
    try:
        response = put_filelist([filepath], user, group, 
                                label, holding_id, tag)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Get files command"""
@nlds_client.command("get")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--target", default=None, type=click.Path())
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
@click.argument("filepath", type=str)
def get(filepath, user, group, target, label, holding_id, tag):
    try:
        response = get_filelist([filepath], user, group, target, 
                                label, holding_id, tag)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Put filelist command"""
@nlds_client.command("putlist")
@click.argument("filelist", type=str)
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
def putlist(filelist, user, group, label, holding_id, tag):
    # read the filelist from the file
    try:
        fh = open(filelist)
        files = fh.readlines()
        fh.close()
    except FileNotFoundError as fe:
        raise click.UsageError(fe)

    try:
        response = put_filelist(files, user, group, 
                                label, holding_id, tag)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Get filelist command"""
@nlds_client.command("getlist")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--target", default=None, type=click.Path(exists=True))
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
@click.argument("filelist", type=str)
def getlist(filelist, user, group, target, label, holding_id, tag):
    # read the filelist from the file
    try:
        fh = open(filelist)
        files = fh.readlines()
        fh.close()
    except FileNotFoundError as fe:
        raise click.UsageError(fe)

    try:
        response = get_filelist(files, user, group, 
                                target, holding_id, tag)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)

def format_request_details(user, group, label=None, holding_id=None, 
                           tag=None, transaction_id=None, sub_id=None,
                           state=None, retry_count=None):
    config = load_config()
    out = ""
    user = get_user(config, user)
    out += f"user: {user}, "
    
    group = get_group(config, group)
    out += f"group: {group}, "

    if label:
        out += f"label: {label}, "
    if holding_id:
        out += f"holding_id: {holding_id}, "
    if tag:
        out += f"tag: {tag}, "
    if transaction_id:
        out += f"transaction_id: {transaction_id}"
    if sub_id:
        out += f"sub_id: {sub_id}"
    if state:
        out += f"state: {state}"
    if retry_count:
        out += f"retry_count: {retry_count}"
    return out[:-2]

def print_list(response: dict, req_details):
    """Print out the response from the list command"""
    list_string = "Listing holding(s) for: "
    list_string += req_details
    print(list_string)
    for h in response['data']['holdings']:
        print(h)

def print_stat(response: dict, req_details):
    """Print out the response from the list command"""
    stat_string = "State of transactions(s) for: "
    stat_string += req_details
    print(stat_string)
    for r in response['data']['records']:
        print(r)

def print_find(response:dict, req_details):
    """Print out the response from the find command"""

"""List (holdings) command"""
@nlds_client.command("list")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
def list(user, group, label, holding_id, tag):
    # 
    try:
        response = list_holding(user, group, label, holding_id, tag)
        req_details = format_request_details(
                user, group, label=label, holding_id=holding_id, tag=tag
            )
        if response['success'] and len(response['data']['holdings']) > 0:
            print_list(response, req_details)
        else:
            fail_string = "Failed to list holding with "
            fail_string += req_details
            raise click.UsageError(fail_string)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)

"""Stat (monitoring) command"""
@nlds_client.command("stat")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--transaction_id", default=None, type=str)
@click.option("--sub_id", default=None, type=str)
@click.option("--state", default=None, type=(str, int))
@click.option("--retry_count", default=None, type=int)
def stat(user, group, transaction_id, sub_id, state, retry_count):
    try:
        response = monitor_transactions(user, group, transaction_id, sub_id,
                                        state, retry_count)
        req_details = format_request_details(
                user, group, transaction_id=transaction_id, sub_id=sub_id, 
                state=state, retry_count=retry_count
            )
        print_stat(response, req_details)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)

"""Find (files) command"""
@nlds_client.command("find")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--path", default=None, type=str)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
def list(user, group, label, holding_id, tag):
    # 
    try:
        response = find_file(user, group, label, holding_id, path, tag)
        req_details = format_request_details(
                user, group, label, holding_id, tag
            )
        if response['success'] and len(response['data']['holdings']) > 0:
            print_find(response, req_details)
        else:
            fail_string = "Failed to list files with "
            fail_string += req_details
            raise click.UsageError(fail_string)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


def main():
    nlds_client(prog_name="nlds")

if __name__ == "__main__":
    nlds_client()
