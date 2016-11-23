__version__ = '1.0.31'

__all__ = ['Host', 'TCPServiceClient', 'TCPService', 'HTTPService', 'HTTPServiceClient', 'api', 'request', 'subscribe',
           'publish', 'xsubscribe', 'get', 'post', 'head', 'put', 'patch', 'delete', 'options', 'trace',
           'Registry', 'RequestException', 'Response', 'Request', 'log', 'setup_logging',
           'apideprecated', 'TrellioServiceException', 'TrellioServiceError', '__version__']

import asyncio

import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from .exceptions import RequestException, TrellioServiceError, TrellioServiceException  # noqa
from .host import Host  # noqa
from .registry import Registry  # noqa
from .services import (TCPService, HTTPService, HTTPServiceClient, TCPServiceClient)  # noqa
from .services import (api, request, subscribe, publish, xsubscribe, apideprecated)  # noqa
from .services import (get, post, head, put, patch, delete, options, trace)  # noqa
from .utils import log  # noqa
from .utils.log import setup_logging  # noqa
from .wrappers import Response, Request  # noqa
