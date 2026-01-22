.. _configuration:

.. |br| raw:: html

  <br/>

Configuration File
==================

Overview
--------

 .. note::
    As of January 2026, and v1.0.17 of the NLDS, the ``nlds init`` command can fill in all of the required values in the ``~/.nlds-config`` file.  This is much more user-friendly and editing of the config file is no longer needed.
    This section is retained as documentation in case the config file does need to be
    edited.

When the user invokes ``nlds`` from the command line or issues a command
from the ``nlds_client.clientlib`` API, a configuration file is required in the 
user's home directory with the path: ``~/.nlds-config``

This configuration file is JSON formatted and contains information required to perform
NLDS requests, including the URL of the NLDS server, the user's details and the 
authentication credentials required by:

  * The OAuth server
  * The object storage cache

It also contains the default user and group to use when issuing a request to the
NLDS.  These can be overriden by the ``-u|--user`` and ``-g|--group`` command
line options.

Finally, it contains the URL of the server and the API version, and the location
of the OAuth token file that is also created the first time the ``nlds`` command
is invoked.

An example configuration file is shown below.  

::

    {
        "server" : {
            "url" : "{{ nlds_api_url }}",
            "api" : "{{ nlds_api_version }}"
        },
        "user" : {
            "default_user" : "{{ user_name }}",
            "default_group" : "{{ user_gws }}"
        },
        "authentication" : {
            "oauth_client_id" : "{{ oauth_client_id }}",
            "oauth_client_secret" : "{{ oauth_client_secret }}",
            "oauth_token_url" : "{{ oauth_token_url }}",
            "oauth_scopes" : "{{ oauth_scopes }}",
            "oauth_token_file_location" : "~/.nlds-token"
        },
        "object_storage" : {
            "tenancy"    : "{{ object_store_tenancy }}",
            "access_key" : "{{ object_store_access_key }}",
            "secret_key" : "{{ object_store_secret_key }}"

        },
        "options": {
            "verify_certificates": true
        }
    }

The values for the authentication section have been redacted for this 
documentation, we recommend you use the ``init`` command to populate them.

.. _init:

The init command
----------------

To initialise the NLDS config file, run the command:

::  
    
    nlds init -u <user> -g <group> -U url <NLDS server URL> -k

where the options are:

::

  -u, --user TEXT   Default user to use with nlds.
  -g, --group TEXT  Default group to use with nlds.
  -k, --insecure    Boolean flag to control whether to turn off verification
                    of ssl certificates during request. Defaults to ``false``,
                    only needs to be ``true`` for the staging/test version of
                    the NLDS.
  -U, --url TEXT    Url to use for getting config info. Must start with
                    ``http(s)://``
  --help            Show this message and exit.

Most of these options can be omitted:

* If the ``-u|--user`` option is omitted, then the user's login username will be used.  On JASMIN, this will be your JASMIN username.
* If the ``-g|--group`` option is omitted, then the first group the user belongs to will be used.  On JASMIN this is typically ``users``.  This is not really suitable, a group workspace group that the user belongs to should be used.
* If the ``-U|--url`` option is omitted, then the default URL will be used.  This is the location of the NLDS service, so this option should be omitted in most cases.
* If the ``-k|--insecure`` option is omitted, then a secure connection will be used.  This is the default option, so this option should be omitted in most cases, to ensure a secure connection.

As a minimum, and in most cases for most NLDS users, only the ``-g|--group`` option is required.  This should be a group workspace (GWS) that you belong to, and want to use as your default GWS. i.e.

::

    nlds init -g <gws_group>

will create and fill your ``~/.nlds-config`` file.  It will ask for your JASMIN password, which should be the one used for your login username to log into JASMIN.
In conjunction with the username and password, this command will:

#.  Fill out the location of the NLDS server in the ``{{ nlds_api_url }}`` field.
#.  Fill out the api version of NLDS in the ``{{ nlds_api_version }}`` field.
#.  Fill out the value of ``{{ user_name }}`` from either the login username, or the ``-u|--user`` option if supplied.
#.  Fill out the value of ``{{ user_gws }}`` from either the first group of the user, or the ``-g|--group`` option if supplied.
#.  Fill out the required values for the ``authentication`` section of the config file. This includes the values for ``{{ oauth_client_id }}, {{ oauth_client_secret }}, {{ oauth_token_url }}`` and ``{{ oauth_scopes }}``
#.  Fetch a valid OAuth token and save it to a file at the path indicated by ``oauth_token_file_location``.  The default is ``~/.nlds-token``, i.e. in your home directory.
#.  Fetch valid access and secret keys for the object store and write them into the config file at ``{{ object_store_access_key }}`` and ``{{ object_store_secret_key }}``.
#.  Fill out the correct URL for the object store in the ``{{ tenanacy }}`` field.
#.  Fill out the ``{{ verify_certificates }}`` field based on the ``-k|--insecure`` option.
