
class TrellioServiceException(Exception):

    """
    To be subclassed by service level exceptions and indicate exceptions that
    are to be handled at the service level itself.
    These exceptions shall not be counted as errors at the macroscopic level.
    eg: record not found, invalid parameter etc.
    """


class TrellioServiceError(Exception):

    """
    Unlike TrellioServiceExceptions these will be counted as errors and must only
    be used when a service encounters an error it couldn't handle at its level.
    eg: client not found, database disconnected.
    """


class TrellioException(Exception):
    pass


class RequestException(Exception):
    pass


class ClientException(Exception):
    pass


class ClientNotFoundError(ClientException):
    pass


class ClientDisconnected(ClientException):
    pass
