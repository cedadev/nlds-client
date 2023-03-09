Configuration File
==================

When the user first invokes ``nlds`` from the command line or issues a command
from the ``nlds_client.clientlib`` API, a configuration file is required in the 
user's home directory with the path:

``~/.nlds-config``

This configuration file is JSON formatted and contains the authentication
credentials required by:

  * The OAuth server.
  * The Object Storage

It also contains the default user and group to use when issuing a request to the
NLDS.  These can be overriden by the ``-u|--user`` and ``-g|--group`` command
line options.

Finally, it contains the URL of the server and the API version, and the location
of the OAuth token file that is also created the first time the ``nlds`` command
is invoked.

An example configuration file is shown below.  Authentication details have been
have been redacted.  You will have to contact the service provider to gain these
credentials.

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
            "access_key" : "{{ object_store_access_key }}",
            "secret_key" : "{{ object_store_secret_key }}"

        },
        "option" : {
            "resolve_filenames" : "false"
        }
    }
