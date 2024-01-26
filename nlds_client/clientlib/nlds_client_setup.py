import os

def get_config_file_location():
    CONFIG_DIR = os.environ["HOME"]
    return CONFIG_DIR + "/.nlds-config"

CONFIG_FILE_LOCATION = get_config_file_location()
DEFAULT_SERVER_URL = "https://nlds.jasmin.ac.uk"
