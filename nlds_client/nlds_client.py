#! /usr/bin/env python
import click
from nlds_client.clientlib.transactions import (get_filelist, put_filelist,
                                                list_holding, find_file,
                                                monitor_transactions,
                                                change_metadata)
from nlds_client.clientlib.exceptions import ConnectionError, RequestError, \
                                             AuthenticationError
from nlds_client.clientlib.config import get_user, get_group, load_config

json=False

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


def integer_permissions_to_string(intperm):
    octal = oct(intperm)[2:]
    result = ""
    value_letters = [(4,"r"),(2,"w"),(1,"x")]
    # Iterate over each of the digits in octal
    for digit in [int(n) for n in str(octal)]:
        # Check for each of the permissions values
        for value, letter in value_letters:
            if digit >= value:
                result += letter
                digit -= value
            else:
                result += '-'
    return result


def pretty_size(size):
    '''Returns file size in human readable format'''

    suffixes = [("B", 1), 
                ("K", 1000), 
                ("M", 1000000), 
                ("G", 1000000000), 
                ("T", 1000000000000)]
    level_up_factor = 2000.0
    for suf, multipler in suffixes:
        if float(size) / multipler > level_up_factor:
            continue
        else:
            return round(size / float(multipler), 2).__str__() + suf
    return round(size / float(multipler), 2).__str__() + suf


def format_request_details(user, group, label=None, holding_id=None, 
                           tag=None, transaction_id=None, sub_id=None,
                           state=None, retry_count=None):
    config = load_config()
    out = ""
    user = get_user(config, user)
    out += f"user:{user}, "
    
    group = get_group(config, group)
    out += f"group:{group}, "

    if label:
        out += f"label:{label}, "
    if holding_id:
        out += f"holding_id:{holding_id}, "
    if tag:
        out += f"tag:{tag}, "
    if transaction_id:
        out += f"transaction_id:{transaction_id}, "
    if sub_id:
        out += f"sub_id:{sub_id}, "
    if state:
        out += f"state:{state}, "
    if retry_count:
        out += f"retry_count:{retry_count}, "
    return out[:-2]


def print_list(response: dict, req_details):
    """Print out the response from the list command"""
    n_holdings = len(response['data']['holdings'])
    list_string = "Listing holding" 
    if n_holdings > 1:
        list_string += "s"
    list_string += " for: "
    list_string += req_details
    click.echo(list_string)
    if n_holdings == 1:
        h = response['data']['holdings'][0]
        click.echo(f"{'':<4}{'id':<16}: {h['id']}")
        click.echo(f"{'':<4}{'label':<16}: {h['label']}")
        click.echo(f"{'':<4}{'user':<16}: {h['user']}")
        click.echo(f"{'':<4}{'group':<16}: {h['group']}")
    else:
        click.echo(f"{'':<4}{'id':<6}{'label':<16}{'user':<16}{'group':<16}")
        for h in response['data']['holdings']:
            click.echo(
                f"{'':<4}{h['id']:<6}{h['label']:<16}{h['user']:<16}{h['group']:<16}"
            )


def print_stat(response: dict, req_details):
    """Print out the response from the list command"""
    stat_string = "State of transaction(s) for: "
    stat_string += req_details
    print(stat_string)
    for r in response['data']['records']:
        print(r)


def __count_files(response:dict):
    """Count the number of files returned from a find query"""
    n_files = 0
    for h in response['data']['holdings']:
        holding = response['data']['holdings'][h]
        for t in holding['transactions']:
            transaction = holding['transactions'][t]
            n_files += len(transaction['filelist'])
    return n_files


def print_single_file(response):
    """Print (full) details of one file"""
    # NRM - note: still using loops over dictionary keys as its
    # 1. easier than trying to just use the first key
    # 2. a bit more robust - in case more than one file matches, for example, in
    # separate holdings
    for hkey in response['data']['holdings']:
        h = response['data']['holdings'][hkey]
        for tkey in h['transactions']:
            t = h['transactions'][tkey]
            time = t['ingest_time'].replace("T", " ")
            for f in t['filelist']:
                click.echo(f"{'':<4}{'path':<16}: {f['original_path']}")
                click.echo(f"{'':<4}{'type':<16}: {f['path_type']}")
                if (f['link_path']):
                    click.echo(f"{'':<4}{'link path':<16}: {f['link_path']}")
                size = pretty_size(f['size'])
                click.echo(f"{'':<4}{'size':<16}: {size}")
                click.echo(f"{'':<4}{'user uid':<16}: {f['user']}")
                click.echo(f"{'':<4}{'group gid':<16}: {f['group']}")
                click.echo(
                    f"{'':<4}{'permissions':<16}: "
                    f"{integer_permissions_to_string(f['permissions'])}"
                )
                click.echo(f"{'':<4}{'ingest time':<16}: {time}")
                # locations
                stls = " "
                for s in f['locations']:
                    stls += s['storage_type']+", "

                click.echo(f"{'':<4}{'storage location':<16}:{stls[0:-2]}")


def print_multi_file(response):
    click.echo(f"{'':<4}{'h-id':<6}{'h-label':<16}{'path':<64}{'size':<8}{'time':<12}")
    for hkey in response['data']['holdings']:
        h = response['data']['holdings'][hkey]
        for tkey in h['transactions']:
            t = h['transactions'][tkey]
            time = t['ingest_time'].replace("T", " ")
            for f in t['filelist']:
                size = pretty_size(f['size'])
                click.echo(f"{'':4}{h['holding_id']:<6}{h['label']:<16}"
                           f"{f['original_path']:<64}{size:<8}"
                           f"{time:<12}")

def print_find(response:dict, req_details):
    """Print out the response from the find command"""
    n_holdings = len(response['data']['holdings'])
    list_string = "Listing files for holding"
    if n_holdings > 1:
        list_string += "s"
    list_string += " for: "
    list_string += req_details
    click.echo(list_string)
    # get total number of files
    n_files = __count_files(response)
    if (n_files == 1):
        print_single_file(response)
    else:
        print_multi_file(response)


def print_meta(response:dict, req_details):
    """Print out the response from the meta command"""
    print(response)


"""Put files command"""
@nlds_client.command("put")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
@click.option("--json", default=False, type=bool)
@click.argument("filepath", type=str)
def put(filepath, user, group, label, holding_id, tag, json):
    try:
        response = put_filelist([filepath], user, group, 
                                label, holding_id, tag)
        if json:
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
@click.option("--json", default=False, type=bool)
@click.argument("filepath", type=str)
def get(filepath, user, group, target, label, holding_id, tag, json):
    try:
        response = get_filelist([filepath], user, group, target, 
                                label, holding_id, tag)
        if json:
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
@click.option("--json", default=False, type=bool)
def putlist(filelist, user, group, label, holding_id, tag, json):
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
        if json:
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
@click.option("--json", default=False, type=bool)
@click.argument("filelist", type=str)
def getlist(filelist, user, group, target, label, holding_id, tag, json):
    # read the filelist from the file
    try:
        fh = open(filelist)
        files = fh.readlines()
        fh.close()
    except FileNotFoundError as fe:
        raise click.UsageError(fe)

    try:
        response = get_filelist(files, user, group, 
                                target, label, holding_id, tag)
        if json:
            print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""List (holdings) command"""
@nlds_client.command("list")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
@click.option("--json", default=False, is_flag=True)
def list(user, group, label, holding_id, tag, json):
    # 
    try:
        response = list_holding(user, group, label, holding_id, tag)
        req_details = format_request_details(
                user, group, label=label, holding_id=holding_id, tag=tag
            )
        if response['success']:
            if json:
                print(response)
            else:
                print_list(response, req_details)
        else:
            fail_string = "Failed to list holding with "
            fail_string += req_details
            if 'failure' in response['details']:
                fail_string += "\nReason: " + response['details']['failure']
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
@click.option("--state", default=None, type=str)
@click.option("--retry_count", default=None, type=int)
@click.option("--json", default=False, type=bool, is_flag=True)
def stat(user, group, transaction_id, sub_id, state, retry_count, json):
    try:
        response = monitor_transactions(user, group, transaction_id, sub_id,
                                        state, retry_count)
        req_details = format_request_details(
                user, group, transaction_id=transaction_id, sub_id=sub_id, 
                state=state, retry_count=retry_count
            )
        if response['success']:
            if json:
                print(response)
            else:
                print_stat(response, req_details)
        else:
            fail_string = "Failed to get status of transaction(s) with "
            fail_string += req_details
            if 'failure' in response['details']:
                fail_string += "\nReason: " + response['details']['failure']
            raise click.UsageError(fail_string)
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
@click.option("--json", default=False, type=bool, is_flag=True)
def find(user, group, label, holding_id, path, tag, json):
    # 
    try:
        response = find_file(user, group, label, holding_id, path, tag)
        req_details = format_request_details(
                user, group, label, holding_id, tag
            )
        if response['success']:
            if json:
                print(response)
            else:
                print_find(response, req_details)
        else:
            fail_string = "Failed to list files with "
            fail_string += req_details
            if response['details']['failure']:
                fail_string += "\n" + response['details']['failure']
            raise click.UsageError(fail_string)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)

"""Meta command"""
@nlds_client.command("meta")
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--label", default=None, type=str)
@click.option("--holding_id", default=None, type=int)
@click.option("--tag", default=None, type=TAG_PARAM_TYPE)
@click.option("--new_label", default=None, type=str)
@click.option("--new_tag", default=None, type=TAG_PARAM_TYPE)
@click.option("--json", default=False, type=bool, is_flag=True)
def meta(user, group, label, holding_id, tag, new_label, new_tag, json):
    # 
    try:
        response = change_metadata(user, group, label, holding_id, tag,
                                   new_label, new_tag)
        req_details = format_request_details(
                user, group, label, holding_id, tag
            )
        if response['success'] > 0:
            if json:
                print_meta(response, req_details)
            else:
                print(response)
        else:
            fail_string = "Failed to list files with "
            fail_string += req_details
            if response['details']['failure']:
                fail_string += "\n" + response['details']['failure']
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
