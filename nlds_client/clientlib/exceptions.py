"""Custom exceptions"""

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