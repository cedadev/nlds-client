import json
import os.path
from nlds_client.clientlib.nlds_client_setup import CONFIG_FILE_LOCATION
from nlds_client.clientlib.exceptions import ConfigError

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
            value = server_section[key]
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
            value = auth_section[key]
        except KeyError:
            raise ConfigError(
                f"The config file at {CONFIG_FILE_LOCATION} does not contain "
                f"{key} in ['authentication'] section."
            )


def load_config():
    """Config file for the client contains:
        authentication : {
            oauth_client_id : <client id>,
            oauth_client_secret : <client secret>,
            oauth_token_url : <token url>,
            oauth_token_introspect_url : <token introspect url>
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
