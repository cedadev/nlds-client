CEDA Near-Line Data Store Client
================================

This is the client used for interacting with the CEDA Near-Line Data Store
([NLDS](https://github.com/cedadev/nlds)).

It consists of a library part (clientlib) and a command line client
(nlds_client.py)

NLDS client is built upon [Requests](https://docs.python-requests.org/en/master/index.html) and [Click](https://click.palletsprojects.com/en/8.0.x/)

NLDS client requires Python 3.  It has been tested with Python 3.8 and Python 3.9.

Installation
------------

1.  Create a Python virtual environment:
    `python3 -m venv ~/nlds-client`

2.  Activate the nlds-client:
    `source ~/nlds-client/bin/activate`

3.  Install the nlds-client package with editing capability:
    `pip install git+https://github.com/cedadev/nlds-client.git@development#egg=nlds-client`

Using
-----

Using the pip install method, an alias for the NLDS client is created: `nlds`.
This can be used to `PUT` and `GET` files and filelists to the NLDS server.

Config
------
NLDS client requires a config file in the user's home directory: `~/.nlds-config`.  This file contains information about the JASMIN infrastructure and so is not included in the GitHub repository.  A Jinja-2 template is included in the `nlds_client/templates/nlds-config.j2` file.

This config file requires information about the JASMIN OAuth2 authentication server, including the `oauth_client_id`, `oauth_client_secret` and various URLs.

When the NLDS client is first used, the user will be prompted to enter their username and password.  This is the username and password for the JASMIN accounts portal.

The token is stored at a location defined in the `~/.nlds-config` file with the key `oauth_token_file_location`.
