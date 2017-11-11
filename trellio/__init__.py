__all__ = ['Host', 'TCPServiceClient', 'TCPService', 'HTTPService', 'HTTPServiceClient', 'api', 'request', 'subscribe',
           'publish', 'xsubscribe', 'get', 'post', 'head', 'put', 'patch', 'delete', 'options', 'trace',
           'RequestException', 'Response', 'Request', 'log', 'setup_logging', 'apideprecated',
           'TrellioServiceException', 'TrellioServiceError', 'ConfigHandler', 'ManagementCommand', 'HTTPView',
           'TCPView', 'ManagementRegistry', 'InvalidCMDArguments', 'execute_from_command_line', 'Publisher',
           'Subscriber']

import logging

logger = logging.getLogger(__name__)

try:
    import asyncio
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    logger.warning('uvloop is not installed, event loop will be set to default asyncio loop')

from .conf_manager import *
from .exceptions import RequestException, TrellioServiceError, TrellioServiceException  # noqa
from .host import Host  # noqa
from .management import *
from .pubsub import Publisher, Subscriber
from .services import (TCPService, HTTPService, HTTPServiceClient, TCPServiceClient)  # noqa
from .services import (api, request, subscribe, publish, xsubscribe, apideprecated)  # noqa
from .services import (get, post, head, put, patch, delete, options, trace)  # noqa
from .utils import log  # noqa
from .utils.log import setup_logging  # noqa
from .views import HTTPView, TCPView
from .wrappers import Response, Request  # noqa

__version__ = '1.1.34rc3'
