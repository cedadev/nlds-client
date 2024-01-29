CEDA Near-Line Data Store Client
================================

For more information please see the [documentation](https://cedadev.github.io/nlds-client/index.html).

This is the client used for interacting with the CEDA Near-Line Data Store
([NLDS](https://github.com/cedadev/nlds)).

It consists of a library part (clientlib) and a command line client
(nlds_client.py)

NLDS client is built upon [Requests](https://docs.python-requests.org/en/master/index.html) and [Click](https://click.palletsprojects.com/en/8.0.x/)

NLDS client requires Python 3.  It has been tested with Python 3.8, 3.9, 3.10 
and 3.11.

Installation
------------

1.  Create a python virtual environment:
    ``` bash
    python3 -m venv ~/nlds-client
    ```

2.  Activate your new virtual environment:
    ``` bash
    source ~/nlds-client/bin/activate
    ```

3.  Install the nlds-client package directly from this github repo:
    ``` bash
    pip install git+https://github.com/cedadev/nlds-client.git
    ```

If installing this repository for development we recommend you install with the 
editable flag (`-e`).  

Config
------
NLDS client requires a config file in the user's home directory: `~/.nlds-config`.  This file contains information about the JASMIN infrastructure and so is not included in the GitHub repository. A Jinja-2 template is included in the `nlds_client/templates/nlds-config.j2` file.

This config file requires information about the JASMIN OAuth2 authentication server, including the `oauth_client_id`, `oauth_client_secret` and various URLs. 
These can be populated by using the command

```
nlds init
```

This will need to be pointed at an appropriate NLDS server url but will default to the one hosted on JASMIN - see the [relevant section](https://cedadev.github.io/nlds-client/configuration.html) of the docs for more details.

When the NLDS client is first used, the user will be prompted to enter their username and password.  This is the username and password for the JASMIN accounts portal. 
The token is stored at a location defined in the `~/.nlds-config` file with the key `oauth_token_file_location`.

To use the NLDS you will also need to provide a `token` and `secret_key` to access the object store you would like to use as an NLDS cache. 
Details for how to do this are in the [documentation](https://cedadev.github.io/nlds-client/configuration.html).

Usage
-----

Upon installation, an alias for the NLDS client is created: `nlds`. This can be used to `PUT` and `GET` files and filelists to and from an NLDS server, as well as a whole host of other commands. See the [documentation](https://cedadev.github.io/nlds-client/tutorial.html) for an extensive tutorial. 
A [reference](https://cedadev.github.io/nlds-client/command_ref.html) of all available commands is also available.


Tests
-----

Automatic unit-testing is run with pytest, to manually run the tests for a local development environment, first ensure the appropriate version of pytest is installed in your venv. From the root of the repository, run:

``` bash 
pip install -r tests/requirements.txt
```

and then, similarly from the root of the repo, run the tests with: 

```bash
pytest
```
