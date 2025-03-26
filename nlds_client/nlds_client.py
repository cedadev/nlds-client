#! /usr/bin/env python
""" """
__author__ = "Neil Massey and Jack Leland"
__date__ = "29 Jan 2024"
__copyright__ = "Copyright 2025 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"
__contact__ = "neil.massey@stfc.ac.uk"

from json import dumps as json_dumps

import click

from nlds_client.clientlib.transactions import (
    get_filelist,
    put_filelist,
    list_holding,
    find_file,
    monitor_transactions,
    get_transaction_state,
    change_metadata,
    init_client,
)
from nlds_client.clientlib.exceptions import (
    ConnectionError,
    RequestError,
    AuthenticationError,
)
from nlds_client.clientlib.config import get_user, get_group, load_config
from nlds_client.clientlib.nlds_client_setup import CONFIG_FILE_LOCATION
from nlds_client import __version__

json = False


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "-v",
    "--version",
    default=False,
    is_flag=True,
    help="Output NLDS client version and exit.",
)
def nlds_client(ctx, version):
    if ctx.invoked_subcommand is None:
        if version:
            click.echo(f"Near Line Data Store client {__version__}.")
            click.echo(
                "Copyright © 2022-2025 Centre of Environmental Data Analysis "
                "Developers, Scientific and Technical Facilities Council (STFC), "
                "UK Research and Innovation (UKRI)"
            )
            click.echo(
                "See https://github.com/cedadev/nlds-client/blob/main/LICENSE.txt for "
                "the full license."
            )
        else:
            click.echo(ctx.get_help())


"""Custom class for tags in the format key:value 
(i.e. using the colon as separator between key and value."""


class TagParamType(click.ParamType):
    name = "tag"

    def __init__(self):
        self.tag_dict = {}

    def convert(self, value, param, ctx):
        try:
            substrs = value.replace(" ", "").split(",")
            for s in substrs:
                k, v = s.split(":")
                self.tag_dict[k] = v
        except ValueError:
            self.fail(f"{value!r} is not a valid (list of) tag(s)", param, ctx)
        return self.tag_dict


def integer_permissions_to_string(intperm):
    octal = oct(intperm)[2:]
    result = ""
    value_letters = [(4, "r"), (2, "w"), (1, "x")]
    # Iterate over each of the digits in octal
    for digit in [int(n) for n in str(octal)]:
        # Check for each of the permissions values
        for value, letter in value_letters:
            if digit >= value:
                result += letter
                digit -= value
            else:
                result += "-"
    return result


def pretty_size(size):
    """Returns file size in human readable format"""

    suffixes = [
        ("B", 1),
        ("K", 1000),
        ("M", 1000000),
        ("G", 1000000000),
        ("T", 1000000000000),
    ]
    level_up_factor = 2000.0
    for suf, multipler in suffixes:
        if float(size) / multipler > level_up_factor:
            continue
        else:
            return round(size / float(multipler), 2).__str__() + suf
    return round(size / float(multipler), 2).__str__() + suf


def format_request_details(
    user,
    group,
    groupall=False,
    label=None,
    holding_id=None,
    tag=None,
    id=None,
    transaction_id=None,
    sub_id=None,
    state=None,
    api_action=None,
    job_label=None,
):
    config = load_config()
    out = ""
    user = get_user(config, user)
    out += f"user:{user}, "

    group = get_group(config, group)
    out += f"group:{group}, "

    if groupall:
        out += f"groupall:{groupall}, "
    if label:
        out += f"label:{label}, "
    if id:
        out += f"id:{id}, "
    if holding_id:
        out += f"holding_id:{holding_id}, "
    if tag:
        out += f"tag:{tag}, "
    if transaction_id:
        out += f"transaction_id:{transaction_id}, "
    if job_label:
        out += f"job_label:{job_label}, "
    if sub_id:
        out += f"sub_id:{sub_id}, "
    if state:
        out += f"state:{state}, "
    if api_action:
        out += f"api-action:{api_action}, "
    return out[:-2]


def _tags_to_str(tags):
    tags_str = ""
    for t in tags:
        tags_str += f"{t} : {tags[t]}\n{'':22}"
    return tags_str


def print_list(response: dict, req_details):
    """Print out the response from the list command"""
    n_holdings = len(response["data"]["holdings"])
    list_string = "Listing holding"
    if n_holdings > 1:
        list_string += "s"
    list_string += " for "
    list_string += req_details
    click.echo(list_string)
    if n_holdings == 1:
        h = response["data"]["holdings"][0]
        click.echo(f"{'':<4}{'user':<16}: {h['user']}")
        click.echo(f"{'':<4}{'group':<16}: {h['group']}")
        click.echo(f"{'':<4}{'id':<16}: {h['id']}")
        click.echo(f"{'':<4}{'label':<16}: {h['label']}")
        click.echo(f"{'':<4}{'ingest time':<16}: {h['date'].replace('T',' ')}")
        if "transactions" in h:
            trans_str = ""
            for t in h["transactions"]:
                trans_str += t + f"\n{'':<22}"
            click.echo(f"{'':<4}{'transaction id':<16}: {trans_str[:-23]}")
        if "tags" in h and len(h["tags"]) > 0:
            tags_str = _tags_to_str(h["tags"])
            click.echo(f"{'':<4}{'tags':<16}: {tags_str[:-23]}")
    else:
        click.echo(f"{'':<4}{'user':<16}{'id':<6}{'label':<16}{'ingest time':<32}")
        for h in response["data"]["holdings"]:
            click.echo(
                f"{'':<4}{h['user']:<16}{h['id']:<6}{h['label']:<16}{h['date'].replace('T',' '):<32}"
            )


def print_single_stat(response: dict, req_details):
    """Print a single status in more detail, with a list of failed files if
    necessary"""
    stat_string = "State of transaction for "
    stat_string += req_details
    click.echo(stat_string)
    # still looping over the keys, just in case more than one state returned
    for tr in response["data"]["records"]:
        state, _ = get_transaction_state(tr)
        if state == None:
            continue
        click.echo(f"{'':<4}{'id':<16}: {tr['id']}")
        click.echo(f"{'':<4}{'user':<16}: {tr['user']}")
        click.echo(f"{'':<4}{'group':<16}: {tr['group']}")
        click.echo(f"{'':<4}{'action':<16}: {tr['api_action']}")
        click.echo(f"{'':<4}{'transaction id':<16}: {tr['transaction_id']}")
        if "label" in tr:
            click.echo(f"{'':<4}{'label':<16}: {tr['label']}")
        click.echo(
            f"{'':<4}{'creation time':<16}: {(tr['creation_time']).replace('T',' ')}"
        )
        click.echo(f"{'':<4}{'state':<16}: {state}")
        if "warnings" in tr:
            warn_str = ""
            for w in tr["warnings"]:
                warn_str += w + f"\n{'':<22}"
            click.echo(f"{'':<4}{'warnings':<16}: {warn_str[:-23]}")

        click.echo(f"{'':<4}{'sub records':<16}->")
        for sr in tr["sub_records"]:
            click.echo(f"{'':4}{'+':<4} {'id':<13}: {sr['id']}")
            click.echo(f"{'':<9}{'sub_id':<13}: {sr['sub_id']}")
            click.echo(f"{'':<9}{'state':<13}: {sr['state']}")
            click.echo(
                f"{'':<9}{'last update':<13}: {(sr['last_updated']).replace('T',' ')}"
            )

            if len(sr["failed_files"]) > 0:
                click.echo(f"{'':<9}{'failed files':<13}->")
                for ff in sr["failed_files"]:
                    click.echo(f"{'':<9}{'+':<4} {'filepath':<8} : {ff['filepath']}")
                    click.echo(f"{'':<9}{'':>4} {'reason':<8} : {ff['reason']}")


def print_multi_stat(response: dict, req_details):
    """Print a multi-line set of status"""
    stat_string = "State of transactions for "
    stat_string += req_details
    click.echo(stat_string)
    click.echo(
        f"{'':<4}{'user':<16}{'id':<12}{'action':<16}{'job label':<16}"
        f"{'label':<16}{'state':<23}{'last update':<20}"
    )
    for tr in response["data"]["records"]:
        state, time = get_transaction_state(tr)
        if state == None:
            continue
        time = time.isoformat().replace("T", " ")
        if "label" in tr:
            label = tr["label"]
        else:
            label = ""
        if "job_label" in tr and tr["job_label"]:
            job_label = tr["job_label"]
        else:
            job_label = ""  # tr['transaction_id'][0:8]
        click.echo(
            f"{'':<4}{tr['user']:<16}{tr['id']:<12}{tr['api_action']:<16}"
            f"{job_label:16}{label:16}"
            f"{state:<23}{time:<20}"
        )


def print_stat(response: dict, req_details):
    """Print out the response from the list command"""
    L = len(response["data"]["records"])
    # L of 0 should be trapped by exceptions on the server
    if L == 1:
        print_single_stat(response, req_details)
    else:
        print_multi_stat(response, req_details)


def __count_files(response: dict):
    """Count the number of files returned from a find query"""
    n_files = 0
    for h in response["data"]["holdings"]:
        holding = response["data"]["holdings"][h]
        for t in holding["transactions"]:
            transaction = holding["transactions"][t]
            n_files += len(transaction["filelist"])
    return n_files


def print_single_file(response, print_url=False):
    """Print (full) details of one file"""
    # NRM - note: still using loops over dictionary keys as its
    # 1. easier than trying to just use the first key
    # 2. a bit more robust - in case more than one file matches, for example, in
    # separate holdings
    for hkey in response["data"]["holdings"]:
        h = response["data"]["holdings"][hkey]
        for tkey in h["transactions"]:
            t = h["transactions"][tkey]
            time = t["ingest_time"].replace("T", " ")
            for f in t["filelist"]:
                click.echo(f"{'':<4}{'path':<16}: {f['original_path']}")
                click.echo(f"{'':<4}{'type':<16}: {f['path_type']}")
                if f["link_path"]:
                    click.echo(f"{'':<4}{'link path':<16}: {f['link_path']}")
                size = pretty_size(f["size"])
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
                url = _get_url_from_file(f)
                for s in f["locations"]:
                    stls += s["storage_type"] + ", "

                click.echo(f"{'':<4}{'storage location':<16}:{stls[0:-2]}")
                if url is not None and print_url:
                    click.echo(f"{'':<4}{'url':<16}: {url}")


def _get_url_from_file(f):
    url = None
    for s in f["locations"]:
        if s["storage_type"] == "OBJECT_STORAGE":
            url = s["url"]
    return url


def print_simple_file(response, print_url=False):
    for hkey in response["data"]["holdings"]:
        h = response["data"]["holdings"][hkey]
        for tkey in h["transactions"]:
            t = h["transactions"][tkey]
            for f in t["filelist"]:
                url = _get_url_from_file(f)
                if print_url and url:
                    click.echo(url)
                else:
                    click.echo(f"{f['original_path']}")


def get_location_letters(locations):
    ll = ""
    for l in locations:
        if l["root"] != "":
            if len(ll) > 0:
                ll += "+"
            ll += l["storage_type"][:1]
    return ll


def print_multi_file(response, print_url):
    click.echo(
        f"{'':<4}{'user':<16}{'h-id':<6}{'h-label':<16}{'size':<8}{'date':<12}{'storage':<8}{'path'}"
    )
    for hkey in response["data"]["holdings"]:
        h = response["data"]["holdings"][hkey]
        for tkey in h["transactions"]:
            t = h["transactions"][tkey]
            time = t["ingest_time"].replace("T", " ")
            for f in t["filelist"]:
                size = pretty_size(f["size"])
                url = _get_url_from_file(f)
                if url and print_url:
                    path_print = _get_url_from_file(f)
                else:
                    path_print = f["original_path"]
                storage = get_location_letters(f["locations"])
                click.echo(
                    f"{'':4}{h['user']:<16}"
                    f"{h['holding_id']:<6}{h['label']:<16}"
                    f"{size:<8}{time[:11]:<12}{storage:^8}{path_print}"
                )


def print_find(response: dict, req_details, simple, url):
    """Print out the response from the find command"""
    n_holdings = len(response["data"]["holdings"])
    if not simple:
        list_string = "Listing files for holding"
        if n_holdings > 1:
            list_string += "s"
        list_string += " for "
        list_string += req_details
        click.echo(list_string)
    # get total number of files
    n_files = __count_files(response)
    if simple:
        print_simple_file(response, url)
    elif n_files == 1:
        print_single_file(response, url)
    else:
        print_multi_file(response, url)


def print_meta(response: dict, req_details: str):
    """Print out the response from the meta command"""
    meta_string = "Changed metadata for holding for "
    meta_string += req_details
    click.echo(meta_string)
    for h in response["data"]["holdings"]:
        click.echo(f"{'':<4}{'id':<4}: {h['id']}")
        click.echo(f"{'':<8}old metadata: ")
        click.echo(f"{'':<12}{'label':<8}: {h['old_meta']['label']}")
        click.echo(f"{'':<12}{'tags':<8}: {h['old_meta']['tags']}")
        click.echo(f"{'':<8}new metadata: ")
        click.echo(f"{'':<12}{'label':<8}: {h['new_meta']['label']}")
        click.echo(f"{'':<12}{'tags':<8}: {h['new_meta']['tags']}")


def print_response(tr: dict):
    if "msg" in tr and len(tr["msg"]) > 0:
        click.echo(tr["msg"])
    if "holding_id" in tr and tr["holding_id"] and tr["holding_id"] > 0:
        click.echo(f"{'':<4}{'id':<16}: {tr['holding_id']}")
    if "user" in tr and len(tr["user"]) > 0:
        click.echo(f"{'':<4}{'user':<16}: {tr['user']}")
    if "group" in tr and len(tr["group"]) > 0:
        click.echo(f"{'':<4}{'group':<16}: {tr['group']}")
    if "api_action" in tr and len(tr["api_action"]) > 0:
        click.echo(f"{'':<4}{'action':<16}: {tr['api_action']}")
    if "job_label" in tr and tr["job_label"] and len(tr["job_label"]) > 0:
        click.echo(f"{'':<4}{'job label':<16}: {tr['job_label']}")
    if (
        "transaction_id" in tr
        and tr["transaction_id"]
        and len(tr["transaction_id"]) > 0
    ):
        click.echo(f"{'':<4}{'transaction id':<16}: {tr['transaction_id']}")
    if "label" in tr and tr["label"] and len(tr["label"]) > 0:
        click.echo(f"{'':<4}{'label':<16}: {tr['label']}")
    if "tag" in tr and tr["tag"] and len(tr["tag"]) > 0:
        tag_str = _tags_to_str(tr["tag"])
        click.echo(f"{'':<4}{'tags':<16}: {tag_str}")


user_help_text = (
    " If no user or group is given then these values will "
    "default to the user:default_user and user:default values "
    "in the ~/.nlds-config file."
)


"""Put files command"""


@nlds_client.command("put", help="Put a single file.")
@click.option(
    "-u", "--user", default=None, type=str, help="The username to put the file for."
)
@click.option(
    "-g", "--group", default=None, type=str, help="The group to put the file for."
)
@click.option(
    "-l",
    "--label",
    default=None,
    type=str,
    help="The label of the holding to put the file into.  If the "
    "holding already exists then the file will be added to it.  If the "
    "holding does not exist then it will be created with the label. "
    "If this option is omitted then a new holding with a random label "
    "will be created.",
)
@click.option(
    "-b",
    "--job_label",
    default=None,
    type=str,
    help="An optional label for the PUT job, that can be viewed when "
    "using the stat command",
)
@click.option(
    "-i",
    "--holding_id",
    default=None,
    type=int,
    help="The numeric id of an existing holding to put the file into.",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=TagParamType(),
    help="The tags of a holding to put the file into.  If a holding "
    "with the tags already exists then the file will the added to "
    "that holding.  If the holding does not exist then it will be "
    "created with the tags and either a random label or a named label,"
    "if the label parameter is also supplied.  The set of tags must "
    "guarantee uniqueness of the holding.",
)
@click.option(
    "-j", "--json", default=False, is_flag=True, help="Output the result as JSON."
)
@click.argument("filepath", type=str)
def put(filepath, user, group, label, job_label, holding_id, tag, json):
    try:
        response = put_filelist(
            [filepath], user, group, job_label, label, holding_id, tag
        )
        if json:
            click.echo(json_dumps(response))
        else:
            print_response(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


user_help_text = (
    " If no user or group is given then these values will "
    "default to the user:default_user and user:default values "
    "in the ~/.nlds-config file."
)

"""Get files command"""


@nlds_client.command("get", help=f"Get a single file.{user_help_text}")
@click.option(
    "-u", "--user", default=None, type=str, help="The username to get a file for."
)
@click.option(
    "-g", "--group", default=None, type=str, help="The group to get a file for."
)
@click.option(
    "-A",
    "--groupall",
    default=False,
    is_flag=True,
    help="Get a file that belongs to a group, rather than a single user",
)
@click.option(
    "-r",
    "--target",
    default=None,
    type=click.Path(exists=True),
    help="The target path for the retrieved file.  Default is to "
    "retrieve the file to its original path.",
)
@click.option(
    "-l",
    "--label",
    default=None,
    type=str,
    help="The label of the holding to retrieve the file from.  This "
    "can be a regular expression (regex).",
)
@click.option(
    "-b",
    "--job_label",
    default=None,
    type=str,
    help="An optional label for the GET job, that can be viewed when "
    "using the stat command",
)
@click.option(
    "-i",
    "--holding_id",
    default=None,
    type=int,
    help="The id of the holding to retrieve the file from.",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=TagParamType(),
    help="The tag(s) of the holding to retrieve the file from.",
)
@click.option(
    "-j", "--json", default=False, is_flag=True, help="Output the result as JSON."
)
@click.argument("filepath", type=str)
def get(
    filepath, user, group, groupall, target, job_label, label, holding_id, tag, json
):
    try:
        response = get_filelist(
            [filepath], user, group, groupall, target, job_label, label, holding_id, tag
        )
        if json:
            click.echo(json_dumps(response))
        else:
            print_response(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


# """delete files command"""


# @nlds_client.command("delete", help=f"Delete a single file.{user_help_text}")
# @click.option(
#     "-u", "--user", default=None, type=str, help="The username to delete a file for."
# )
# @click.option(
#     "-g", "--group", default=None, type=str, help="The group to delete a file for."
# )
# @click.option(
#     "-A",
#     "--groupall",
#     default=False,
#     is_flag=True,
#     help="Get files that belong to a group, rather than a single " "user",
# )
# @click.option(
#     "-l",
#     "--label",
#     default=None,
#     type=str,
#     help="The label of the holding to delete the file from.  This "
#     "can be a regular expression (regex).",
# )
# @click.option(
#     "-b",
#     "--job_label",
#     default=None,
#     type=str,
#     help="An optional label for the DEL job, that can be viewed when "
#     "using the stat command",
# )
# @click.option(
#     "-i",
#     "--holding_id",
#     default=None,
#     type=int,
#     help="The id of the holding to delete the file from.",
# )
# @click.option(
#     "-j", "--json", default=False, is_flag=True, help="Output the result as JSON."
# )
# @click.argument("filepath", type=str)
# def delete(filepath, user, group, groupall, job_label, label, holding_id, json):
#     try:
#         response = del_filelist(
#             [filepath], user, group, groupall, job_label, label, holding_id
#         )
#         if json:
#             click.echo(response)
#         else:
#             print_response(response)
#     except ConnectionError as ce:
#         raise click.UsageError(ce)
#     except AuthenticationError as ae:
#         raise click.UsageError(ae)
#     except RequestError as re:
#         raise click.UsageError(re)


"""Put filelist command"""


@nlds_client.command(
    "putlist", help=f"Put a number of files specified in a list.{user_help_text}"
)
@click.argument("filelist", type=str)
@click.option(
    "-u", "--user", default=None, type=str, help="The username to put files for."
)
@click.option(
    "-g", "--group", default=None, type=str, help="The group to put files for."
)
@click.option(
    "-l",
    "--label",
    default=None,
    type=str,
    help="The label of the holding to put files into.  If the holding "
    "already exists then the files will be added to it.  If the "
    "holding does not exist then it will be created with the label. "
    "If this option is omitted then a new holding with a random label "
    "will be created.",
)
@click.option(
    "-b",
    "--job_label",
    default=None,
    type=str,
    help="An optional label for the PUT job, that can be viewed when "
    "using the stat command",
)
@click.option(
    "-i",
    "--holding_id",
    default=None,
    type=int,
    help="The numeric id of an existing holding to put files into.",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=TagParamType(),
    help="The tags of a holding to put files into.  If a holding "
    "with the tags already exists then the files will the added to "
    "that holding.  If the holding does not exist then it will be "
    "created with the tags and either a random label or a named label,"
    "if the label parameter is also supplied.  The set of tags must "
    "guarantee uniqueness of the holding.",
)
@click.option(
    "-j", "--json", default=False, is_flag=True, help="Output the result as JSON."
)
def putlist(filelist, user, group, label, job_label, holding_id, tag, json):
    # read the filelist from the file
    try:
        fh = open(filelist)
        files = fh.readlines()
        fh.close()
    except FileNotFoundError as fe:
        raise click.UsageError(fe)

    # clean the list of any newlines / spaces
    for i, v in enumerate(files):
        files[i] = v.strip()
        if len(files[i]) == 0:
            files.pop(i)

    try:
        response = put_filelist(files, user, group, job_label, label, holding_id, tag)
        if json:
            click.echo(json_dumps(response))
        else:
            print_response(response)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Get filelist command"""


@nlds_client.command(
    "getlist", help=f"Get a number of files specified in a list.{user_help_text}"
)
@click.option(
    "-u", "--user", default=None, type=str, help="The username to get files for."
)
@click.option(
    "-g", "--group", default=None, type=str, help="The group to get files for."
)
@click.option(
    "-A",
    "--groupall",
    default=False,
    is_flag=True,
    help="Get files that belong to a group, rather than a single user",
)
@click.option(
    "-r",
    "--target",
    default=None,
    type=click.Path(exists=True),
    help="The target path for the retrieved files.  Default is to "
    "retrieve files to their original path.",
)
@click.option(
    "-l",
    "--label",
    default=None,
    type=str,
    help="The label of the holding(s) to retrieve files from.  This "
    "can be a regular expression (regex).",
)
@click.option(
    "-b",
    "--job_label",
    default=None,
    type=str,
    help="An optional label for the GET job, that can be viewed when "
    "using the stat command",
)
@click.option(
    "-i",
    "--holding_id",
    default=None,
    type=int,
    help="The id of the holding to retrieve files from.",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=TagParamType(),
    help="The tag(s) of the holding(s) to retrieve files from.",
)
@click.option(
    "-j", "--json", default=False, is_flag=True, help="Output the result as JSON."
)
@click.argument("filelist", type=str)
def getlist(
    filelist, user, group, groupall, target, job_label, label, holding_id, tag, json
):
    # read the filelist from the file
    try:
        fh = open(filelist)
        files = fh.readlines()
        fh.close()
    except FileNotFoundError as fe:
        raise click.UsageError(fe)

    try:
        response = get_filelist(
            files, user, group, groupall, target, job_label, label, holding_id, tag
        )
        if json:
            click.echo(json_dumps(response))
        else:
            print_response(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


# """dellist files command"""


# @nlds_client.command(
#     "dellist", help=f"Delete a number of files specified in a list.{user_help_text}"
# )
# @click.option(
#     "-u", "--user", default=None, type=str, help="The username to delete files for."
# )
# @click.option(
#     "-g", "--group", default=None, type=str, help="The group to delete files for."
# )
# @click.option(
#     "-A",
#     "--groupall",
#     default=False,
#     is_flag=True,
#     help="Get files that belong to a group, rather than a single " "user",
# )
# @click.option(
#     "-l",
#     "--label",
#     default=None,
#     type=str,
#     help="The label of the holding to delete files from.  This "
#     "can be a regular expression (regex).",
# )
# @click.option(
#     "-b",
#     "--job_label",
#     default=None,
#     type=str,
#     help="An optional label for the DELLIST job, that can be viewed "
#     "when using the stat command",
# )
# @click.option(
#     "-i",
#     "--holding_id",
#     default=None,
#     type=int,
#     help="The id of the holding to delete the file from.",
# )
# @click.option(
#     "-j", "--json", default=False, is_flag=True, help="Output the result as JSON."
# )
# @click.argument("filelist", type=str)
# def dellist(filelist, user, group, groupall, job_label, label, holding_id, json):
#     # read the filelist from the file
#     try:
#         fh = open(filelist)
#         files = fh.readlines()
#         fh.close()
#     except FileNotFoundError as fe:
#         raise click.UsageError(fe)

#     try:
#         req_details = format_request_details(
#             user, group, groupall=groupall, label=label, holding_id=holding_id
#         )
#         response = del_filelist(
#             files, user, group, groupall, job_label, label, holding_id
#         )
#         if response["success"]:
#             if json:
#                 click.echo(response)
#             else:
#                 print_list(response, req_details)
#         else:
#             fail_string = "Failed to delete file(s) with "
#             fail_string += req_details
#             if "failure" in response["details"]:
#                 fail_string += "\nReason: " + response["details"]["failure"]
#             raise click.UsageError(fail_string)

#         if json:
#             click.echo(response)
#         else:
#             print_response(response)
#     except ConnectionError as ce:
#         raise click.UsageError(ce)
#     except AuthenticationError as ae:
#         raise click.UsageError(ae)
#     except RequestError as re:
#         raise click.UsageError(re)


"""List (holdings) command"""


@nlds_client.command("list", help=f"List holdings.{user_help_text}")
@click.option(
    "-u", "--user", default=None, type=str, help="The username to list holdings for."
)
@click.option(
    "-g", "--group", default=None, type=str, help="The group to list holdings for."
)
@click.option(
    "-A",
    "--groupall",
    default=False,
    is_flag=True,
    help="List holdings that belong to a group, rather than a single user",
)
@click.option(
    "-l",
    "--label",
    default=None,
    type=str,
    help="The label of the holding(s) to list.  This can be a regular"
    "expression (regex).",
)
@click.option(
    "-i",
    "--holding_id",
    default=None,
    type=int,
    help="The numeric id of the holding to list.",
)
@click.option(
    "-n",
    "--transaction_id",
    default=None,
    type=str,
    help="The UUID transaction id of the transaction to list.",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=TagParamType(),
    help="The tag(s) of the holding(s) to list.",
)
@click.option(
    "-j", "--json", default=False, is_flag=True, help="Output the result as JSON."
)
@click.option(
    "-x",
    "--regex",
    default=False,
    type=bool,
    is_flag=True,
    help="Use regular expressions in the  label search term.",
)
def list(user, group, groupall, label, holding_id, transaction_id, tag, json, regex):
    #
    try:
        response = list_holding(
            user,
            group,
            groupall=groupall,
            label=label,
            holding_id=holding_id,
            transaction_id=transaction_id,
            tag=tag,
            regex=regex,
        )
        req_details = format_request_details(
            user, group, groupall=groupall, label=label, holding_id=holding_id, tag=tag
        )
        if response["success"]:
            if json:
                click.echo(json_dumps(response))
            else:
                print_list(response, req_details)
        else:
            fail_string = "Failed to list holding with "
            fail_string += req_details
            if "failure" in response["details"]:
                fail_string += "\nReason: " + response["details"]["failure"]
            raise click.UsageError(fail_string)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Stat (monitoring) command"""


@nlds_client.command("stat", help=f"List transactions.{user_help_text}")
@click.option(
    "-u",
    "--user",
    default=None,
    type=str,
    help="The username to list transactions for.",
)
@click.option(
    "-g", "--group", default=None, type=str, help="The group to list transactions for."
)
@click.option(
    "-A",
    "--groupall",
    default=False,
    is_flag=True,
    help="List transactions that belong to a group, rather than a single user",
)
@click.option(
    "-i",
    "--id",
    default=None,
    type=int,
    help="The numeric id of the transaction to list.",
)
@click.option(
    "-n",
    "--transaction_id",
    default=None,
    type=str,
    help="The UUID transaction id of the transaction to list.",
)
@click.option(
    "-b",
    "--job_label",
    default=None,
    type=str,
    help="The job label of the transaction(s) to list.",
)
@click.option(
    "-a",
    "--api_action",
    default=None,
    type=str,
    help="The api action of the transactions to list. Options: "
    "get | put | getlist | putlist",
)
@click.option(
    "-s",
    "--state",
    default=None,
    type=str,
    help="""
The state of the transactions to list.  Options:
INITIALISING | ROUTING | SPLITTING | INDEXING |
CATALOG_PUTTING | TRANSFER_PUTTING | CATALOG_ROLLBACK |
CATALOG_GETTING | ARCHIVE_GETTING | TRANSFER_GETTING |
ARCHIVE_INIT | CATALOG_ARCHIVE_AGGREGATING | ARCHIVE_PUTTING |
CATALOG_ARCHIVE_UPDATING | CATALOG_ARCHIVE_ROLLBACK |
COMPLETE | FAILED | COMPLETE_WITH_ERRORS |
COMPLETE_WITH_WARNINGS
""",
)
@click.option(
    "-j",
    "--json",
    default=False,
    type=bool,
    is_flag=True,
    help="Output the result as JSON.",
)
@click.option(
    "-x",
    "--regex",
    default=False,
    type=bool,
    is_flag=True,
    help="Use regular expressions in the job label search term.",
)
def stat(
    user, group, groupall, id, transaction_id, job_label, api_action, state, json, regex
):
    try:
        response = monitor_transactions(
            user,
            group,
            groupall=groupall,
            idd=id,
            transaction_id=transaction_id,
            job_label=job_label,
            api_action=api_action,
            state=state,
            regex=regex,
        )
        req_details = format_request_details(
            user,
            group,
            groupall=groupall,
            id=id,
            transaction_id=transaction_id,
            state=state,
            job_label=job_label,
            api_action=api_action,
        )
        if response["success"] and len(response["data"]["records"]):
            if json:
                click.echo(json_dumps(response))
            else:
                print_stat(response, req_details)
        else:
            fail_string = "Failed to get status of transaction(s) with "
            fail_string += req_details
            if "failure" in response["details"]:
                fail_string += "\nReason: " + response["details"]["failure"]
            raise click.UsageError(fail_string)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Find (files) command"""


@nlds_client.command("find", help=f"Find and list files.{user_help_text}")
@click.option(
    "-u", "--user", default=None, type=str, help="The username to find files for."
)
@click.option(
    "-g", "--group", default=None, type=str, help="The group to find files for."
)
@click.option(
    "-A",
    "--groupall",
    default=False,
    is_flag=True,
    help="Find files that belong to a group, rather than a single user",
)
@click.option(
    "-l",
    "--label",
    default=None,
    type=str,
    help="The label of the holding which the files belong to.  This "
    "can be a regular expression (regex).",
)
@click.option(
    "-i",
    "--holding_id",
    default=None,
    type=int,
    help="The numeric id of the holding which the files belong to.",
)
@click.option(
    "-n",
    "--transaction_id",
    default=None,
    type=str,
    help="The UUID transaction id of the transaction to list.",
)
@click.option(
    "-p",
    "--path",
    default=None,
    type=str,
    help="The path of the files to find.  This can be a regular expression (regex)",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=TagParamType(),
    help="The tag(s) of the holding(s) to find files within.",
)
@click.option(
    "-j",
    "--json",
    default=False,
    type=bool,
    is_flag=True,
    help="Output the result as JSON.",
)
@click.option(
    "-1",
    "--simple",
    default=False,
    type=bool,
    is_flag=True,
    help="Output the list of files, one per line, filepath only.",
)
@click.option(
    "-U",
    "--url",
    default=False,
    type=bool,
    is_flag=True,
    help="Output the URL for the file on the object storage.",
)
@click.option(
    "-x",
    "--regex",
    default=False,
    type=bool,
    is_flag=True,
    help="Use regular expressions in the path and label search terms.",
)
def find(
    user,
    group,
    groupall,
    label,
    holding_id,
    transaction_id,
    path,
    tag,
    json,
    simple,
    url,
    regex,
):
    #
    try:
        response = find_file(
            user,
            group,
            groupall=groupall,
            label=label,
            holding_id=holding_id,
            transaction_id=transaction_id,
            path=path,
            tag=tag,
            regex=regex,
        )
        req_details = format_request_details(
            user,
            group,
            groupall=groupall,
            label=label,
            holding_id=holding_id,
            tag=tag,
            transaction_id=transaction_id,
        )
        if response["success"]:
            if json:
                click.echo(json_dumps(response))
            else:
                print_find(response, req_details, simple, url)
        else:
            fail_string = "Failed to list files with "
            fail_string += req_details
            if response["details"]["failure"]:
                fail_string += "\nReason: " + response["details"]["failure"]
            raise click.UsageError(fail_string)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Meta command"""


@nlds_client.command("meta", help=f"Alter metadata for a holding.{user_help_text}")
@click.option(
    "-u",
    "--user",
    default=None,
    type=str,
    help="The username to use when changing metadata for a holding.",
)
@click.option(
    "-g",
    "--group",
    default=None,
    type=str,
    help="The group to use when changing metadata for a holding.",
)
@click.option(
    "-l",
    "--label",
    default=None,
    type=str,
    help="The label of the holding to change metadata for.  This can "
    "be a regular expression (regex)",
)
@click.option(
    "-i",
    "--holding_id",
    default=None,
    type=int,
    help="The numeric id of the holding to change metadata for.",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=TagParamType(),
    help="The tag(s) of the holding(s) to change metadata for.",
)
@click.option(
    "-L", "--new_label", default=None, type=str, help="The new label for the holding."
)
@click.option(
    "-T",
    "--new_tag",
    default=None,
    type=TagParamType(),
    help="The new tag(s) for the holding.",
)
@click.option(
    "-D",
    "--del_tag",
    default=None,
    type=TagParamType(),
    help="Delete a tag from the holding.",
)
@click.option(
    "-j",
    "--json",
    default=False,
    type=bool,
    is_flag=True,
    help="Output the result as JSON.",
)
def meta(user, group, label, holding_id, tag, new_label, new_tag, del_tag, json):
    #
    try:
        req_details = format_request_details(
            user, group, label=label, holding_id=holding_id, tag=tag
        )
        response = change_metadata(
            user, group, label, holding_id, tag, new_label, new_tag, del_tag
        )
        if response["success"] > 0:
            if json:
                click.echo(json_dumps(response))
            else:
                print_meta(response, req_details)
        else:
            fail_string = "Failed to change metadata on holding with "
            fail_string += req_details
            if response["details"]["failure"]:
                fail_string += "\n" + response["details"]["failure"]
            raise click.UsageError(fail_string)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


@nlds_client.command(
    "init",
    help=(
        f"Set up the NLDS client on first use. Will either create a new "
        "config file if one doesn't exist or fill the 'authentication' "
        "section with appropriate values if it does."
    ),
)
@click.option(
    "-U",
    "--url",
    default=None,
    type=str,
    help=("Url to use for getting config info. Must start with http(s)://"),
)
@click.option(
    "-k",
    "--insecure",
    is_flag=True,
    default=False,
    help="Boolean flag to control whether to turn off verification of ssl "
    "certificates during request. Defaults to true, only needs to be False"
    " for the staging/test version of the NLDS.",
)
def init(url: str = None, insecure: bool = False):
    click.echo(click.style("Initialising the Near-line Data Store...\n", fg="yellow"))
    try:
        response = init_client(url, verify_certificates=(not insecure))
        if (
            "success" in response and not response["success"]
        ) or "new_config" not in response:
            raise RequestError(f"Could not init NLDS, something has gone wrong")
        success_msg = f"Successfully initialised, "
        path_str = click.style(CONFIG_FILE_LOCATION, fg="yellow")
        if response["new_config"]:
            success_msg += (
                f"a template config file has been created at "
                f"{path_str} with some of the information necessary"
                " to use the NLDS."
            )
        else:
            success_msg += (
                f"the config file at {path_str} has been updated "
                "with some of the necessary information to start "
                "using the NLDS."
            )

        link_str = click.style("https://s3-portal.jasmin.ac.uk/", fg="blue")
        success_msg += (
            "\n\nYou may still need to manually update the fields:"
            "\n - user.default_user \n - user.default_group "
            "\n - object_storage.access_key"
            "\n - object_storage.secret_key"
            "\n - object_storage.tenancy "
            + click.style("(will default to nlds-cache-02 if not set)", fg="yellow")
            + "\n\nThe latter three values can be obtained from the "
            "object store portal for any object stores you have "
            f"access to ({link_str})."
        )
        click.echo(success_msg)

    except ConnectionError as ce:
        raise click.UsageError(ce)
    except RequestError as re:
        raise click.UsageError(re)
    except Exception as e:
        raise click.UsageError(e)


def main():
    nlds_client(prog_name="nlds")


if __name__ == "__main__":
    click.formatting.wrap_text = 80
    nlds_client()
