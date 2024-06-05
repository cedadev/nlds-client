"""
Custom exceptions
"""
__author__ = 'Neil Massey and Jack Leland'
__date__ = '29 Jan 2024'
__copyright__ = 'Copyright 2024 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'neil.massey@stfc.ac.uk'


class ConnectionError(Exception):
    pass

class StatusCodeError(Exception):
    def __init__(self, message, status_code: int=0):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message)

class RequestError(StatusCodeError):
    pass

class AuthenticationError(StatusCodeError):
    pass

class ServerError(Exception):
    pass

class UsageError(Exception):
    pass

class ConfigError(Exception):
    pass

class StateError(Exception):
    pass