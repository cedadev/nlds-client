"""

"""
__author__ = 'Neil Massey and Jack Leland'
__date__ = '29 Jan 2024'
__copyright__ = 'Copyright 2024 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'neil.massey@stfc.ac.uk'

import os

def get_config_file_location():
    CONFIG_DIR = os.environ["HOME"]
    return CONFIG_DIR + "/.nlds-config"

CONFIG_FILE_LOCATION = get_config_file_location()
DEFAULT_SERVER_URL = "https://nlds.jasmin.ac.uk"
