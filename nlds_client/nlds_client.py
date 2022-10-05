#! /usr/bin/env python
import click
from nlds_client.clientlib.transactions import get_file, get_filelist, \
                                               put_file, put_filelist
from nlds_client.clientlib.exceptions import ConnectionError, RequestError, \
                                             AuthenticationError

@click.group()
def nlds_client():
    pass

"""Put files command"""
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.argument("filepath", type=str)
@nlds_client.command()
def put(filepath, user, group):
    try:
        response = put_file(filepath, user, group)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Get files command"""
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--target", default=None, type=click.Path())
@click.option("--holding_transact", default=None, type=str)
@click.argument("filepath", type=str)
@nlds_client.command()
def get(filepath, user, group, target, holding_transact):
    try:
        response = get_file(filepath, user, group, target, holding_transact)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Put filelist command"""
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.argument("filelist", type=str)
@nlds_client.command()
def putlist(filelist, user, group):
    # read the filelist from the file
    try:
        fh = open(filelist)
        files = fh.readlines()
        fh.close()
    except FileNotFoundError as fe:
        raise click.UsageError(fe)

    try:
        response = put_filelist(files, user, group)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)


"""Get filelist command"""
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.option("--target", default=None, type=click.Path(exists=True))
@click.option("--holding_transact", default=None, type=str)
@click.argument("filelist", type=str)
@nlds_client.command()
def getlist(filelist, user, group, target, holding_transact):
    # read the filelist from the file
    try:
        fh = open(filelist)
        files = fh.readlines()
        fh.close()
    except FileNotFoundError as fe:
        raise click.UsageError(fe)

    try:
        response = get_filelist(files, user, group, target, holding_transact)
        print(response)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)

def main():
    nlds_client()

if __name__ == "__main__":
    nlds_client()
