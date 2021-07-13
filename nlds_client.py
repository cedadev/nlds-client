#! /usr/bin/env python
import click
from clientlib.transactions import get_file
from clientlib.exceptions import ConnectionError, RequestError, \
                                 AuthenticationError

@click.command()
@click.option("--user", default=None, type=str)
@click.option("--group", default=None, type=str)
@click.argument("filepath")
# def testclient(filepath, user, group):
#     pass
#
# @testclient.command()
def get(filepath, user, group):
    try:
        get_file(filepath, user, group)
    except ConnectionError as ce:
        raise click.UsageError(ce)
    except AuthenticationError as ae:
        raise click.UsageError(ae)
    except RequestError as re:
        raise click.UsageError(re)

# @testclient.command()
# def put():
#     pass
    # transaction_id = uuid.uuid4()
    # click.echo("PUT command")

if __name__ == "__main__":
    get()
