import json
import os.path

from click import option
from nlds_client.clientlib.nlds_client_setup import get_config_file_location
from nlds_client.clientlib.exceptions import ConfigError

TEMPLATE_FILE_LOCATION = os.path.join(os.path.dirname(__file__), 
                                      '../templates/nlds-config.j2')
CONFIG_FILE_LOCATION = get_config_file_location()

def validate_config_file(json_config):
    """Validate the JSON config file to match the schema in load_config_file."""
    # Server section
    try:
        server_section = json_config["server"]
    except KeyError:
        raise ConfigError(
            f"The config file at {CONFIG_FILE_LOCATION} does not contain a "
             "['server'] section."
        )

    for key in ["url", "api"]:
        try:
            _ = server_section[key]
        except KeyError:
            raise ConfigError(
                f"The config file at {CONFIG_FILE_LOCATION} does not contain "
                f"{key} in ['server_section'] section."
            )

    # authentication section
    try:
        auth_section = json_config["authentication"]
    except KeyError:
        raise ConfigError(
            f"The config file at {CONFIG_FILE_LOCATION} does not contain an "
             "['authentication'] section."
        )

    for key in ["oauth_client_id",
                "oauth_client_secret",
                "oauth_token_url",
                "oauth_scopes",
                "oauth_token_file_location"]:
        try:
            _ = auth_section[key]
        except KeyError:
            raise ConfigError(
                f"The config file at {CONFIG_FILE_LOCATION} does not contain "
                f"{key} in ['authentication'] section."
            )

    # user section
    try:
        user_section = json_config["user"]
    except KeyError:
        raise ConfigError(
            f"The config file at {CONFIG_FILE_LOCATION} does not contain an "
             "['user'] section."
        )

    for key in ["default_user",
                "default_group"]:
        try:
            _ = user_section[key]
        except KeyError:
            raise ConfigError(
                f"The config file at {CONFIG_FILE_LOCATION} does not contain "
                f"{key} in ['user'] section."
            )               
    
    # object_storage section
    try:
        os_section = json_config["object_storage"]
    except KeyError:
        raise ConfigError(
            f"The config file at {CONFIG_FILE_LOCATION} does not contain an "
             "['object_storage'] section."
        )

    for key in ["access_key",       # "tenancy" is optional and will default
                "secret_key"]:      # on the server
        try:
            _ = os_section[key]
        except KeyError:
            raise ConfigError(
                f"The config file at {CONFIG_FILE_LOCATION} does not contain "
                f"{key} in ['object_storage'] section."
            )    

def load_config():
    """Config file for the client contains:
        server : {
            url : <server>,
            api : <version>
        },
        user : {
            default_user : <user>,
            default_group : <group>
        },
        authentication : {
            oauth_client_id : <client_id>,
            oauth_client_secret : <client_secret>,
            oauth_token_url : <token_url>,
            oauth_scopes : <scopes>,
            oauth_token_file_location : <token_location>
        },
        object_storage : {
            tenancy : <os_tenancy> (optional),
            access_key : <os_access_key>,
            secret_key : <os_secret_key>

        }
    """
    # Location of config file is {CONFIG_FILE_LOCATION}.  Open it, checking
    # that it exists as well.
    try:
        fh = open(os.path.expanduser(f"{CONFIG_FILE_LOCATION}"))
    except FileNotFoundError:
        raise FileNotFoundError(
            f"The config file cannot be found {CONFIG_FILE_LOCATION}"
        )

    # Load the JSON file, ensuring it is correctly formatted
    try:
        json_config = json.load(fh)
    except json.JSONDecodeError as je:
        raise ConfigError(
            f"The config file at {CONFIG_FILE_LOCATION} has an error at "
            f"character {je.pos}: {je.msg}."
        )

    # Check that the JSON file contains the correct keywords / is in the correct
    # format
    validate_config_file(json_config)

    return json_config


def create_config(url: str):
    # Read contents of template file 
    with open(os.path.expanduser(f"{TEMPLATE_FILE_LOCATION}"), 'r') as f_templ:
        template_contents = json.load(f_templ)

    # Change the default server to something useable
    template_contents['server']['url'] = url

    # Delete the tenancy option from the config so the user doesn't 
    # accidentally leave it empty
    del template_contents["object_storage"]["tenancy"]

    # Location of config file should be {CONFIG_FILE_LOCATION}. Create it and 
    # fail if it already exists 
    with open(os.path.expanduser(f"{CONFIG_FILE_LOCATION}"), 'x') as f:
        json.dump(template_contents, f, indent=4)

    # Lastly, validate the config file to make sure we're not missing anyhting
    validate_config_file(template_contents)

    return template_contents


def write_auth_section(config, auth_config, url: str = None):
    # Second, validate the config again and make sure we're not missing anything
    validate_config_file(config)

    # Overwrite the authentication block with the one given and write it back to 
    # the file
    config['authentication'] |= auth_config
    with open(os.path.expanduser(f"{CONFIG_FILE_LOCATION}"), 'w') as f:
        json.dump(config, f, indent=4)


def get_user(config, user):
    """Get the user from either the function parameter or the config."""
    user = user
    if (user is None and
        "user" in config and
        "default_user" in config["user"]):
        user = config["user"]["default_user"]
    return user


def get_group(config, group):
    """Get the group from either the function parameter or the config."""
    group = group
    if (group is None and
        "user" in config and
        "default_group" in config["user"]):
        group = config["user"]["default_group"]
    return group


_DEFAULT_OPTIONS = {
    "verify_certificates": True,
    "resolve_filenames": True
}
def get_option(config, option_name, section_name='option'):
    """Get an option from either the config or the DEFAULT_OPTIONS dict."""
    if (section_name in config and
        # Get value from config if option section and option present
        option_name in config[section_name]):
        option_value = config[section_name][option_name]
    elif option_name in _DEFAULT_OPTIONS:
        # Otherwise get the default value 
        option_value = _DEFAULT_OPTIONS[option_name]
    else:
        # Silently fail if option not specified in _DEFAULT_OPTIONS
        option_value = None
    return option_value


def get_tenancy(config):
    """Get the object storage tenancy from the config file.  This is optional
    so could be None."""
    tenancy = None
    if ("object_storage" in config and
        "tenancy" in config["object_storage"]):
        tenancy = config["object_storage"]["tenancy"]
    return tenancy
    

def get_access_key(config):
    """Get the object storage access key from the config file. """
    access_key = ""
    if ("object_storage" in config and
        "access_key" in config["object_storage"]):
        access_key = config["object_storage"]["access_key"]
    return access_key


def get_secret_key(config):
    """Get the object storage secret key from the config file. """
    secret_key = ""
    if ("object_storage" in config and
        "secret_key" in config["object_storage"]):
        secret_key = config["object_storage"]["secret_key"]
    return secret_key