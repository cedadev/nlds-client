.. _configuration:

Configuration File
==================

When the user first invokes ``nlds`` from the command line or issues a command
from the ``nlds_client.clientlib`` API, a configuration file is required in the 
user's home directory with the path:

``~/.nlds-config``

This configuration file is JSON formatted and contains the authentication
credentials required by:

  * The OAuth server
  * The Object Storage cache

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
            "oauth_scopes" : "{{ oauth_scopes }}"",
            "oauth_token_file_location" : "~/.nlds-token"
        },
        "object_storage" : {
            "tenancy"    : "{{ object_store_tenancy }}",
            "access_key" : "{{ object_store_access_key }}",
            "secret_key" : "{{ object_store_secret_key }}"

        },
        "option" : {
            "resolve_filenames" : "false"
        }
    }

The values for the authentication section have been redacted for this 
documentation, we recommend you use the ``init`` command to populate them.

.. _init:

The init command
----------------

The required values for the ``authentication`` section of the config file can be 
obtained via the ``nlds init`` command, which will get values for each of the 
the ``oauth_`` keys in the ``authentication`` section of the config and insert 
them either (a) into an existing config, or (b) into a blank template config 
file if one doesn't already exist at the expected path in the user's home 
directory. This will get you started if you don't already have a fully filled-in 
config file. Note however that the oauth_token_file_location will not be 
altered.  For more information about this command please see the relevant part 
of the :ref:`API reference<command-ref>` section.  

.. note::
    If you are taking part in the ``nlds`` beta testing program, you will also 
    need to specify a url with the ``-u`` switch and turn off ssl verification 
    with the ``-k`` flag, so your init command will look a bit like this:

    .. code-block:: bash

        > nlds init -u {{ nlds-testing-url }} -k
    
    but with the ``{{ nlds-testing-url }}`` replaced with the url provided to 
    you by the JASMIN staff. 


The init command will not populate the ``default_user`` or ``default_group``, so
these will have to be filled in with the relevant user and group-workspace for 
your use case. The ``access_key`` and ``secret_key`` will also need to be 
populated with a ``token`` and ``secret_key`` generated on the 
`object-store portal <https://s3-portal.jasmin.ac.uk/login>`_ for the 
appropriate ``tenancy`` you wish to use. In most cases this will be the default 
``nlds-cache-02-o``, so we recommend that, unless you know what you are doing, 
the ``tenancy`` field should just be omitted.
