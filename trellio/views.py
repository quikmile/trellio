__all__ = ['HTTPView', 'TCPView']

from .utils.helpers import default_preflight_response
from .utils.ordered_class_member import OrderedClassMembers


class BaseView:
    '''base class for views'''
    _host = None

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host


class BaseHTTPView(BaseView, metaclass=OrderedClassMembers):
    '''base class for HTTP views'''
    middlewares = []

    def __init__(self):
        super(BaseHTTPView, self).__init__()


class HTTPView(BaseHTTPView):
    def __init__(self, allow_cross_domain=True,
                 preflight_response=default_preflight_response):
        super(HTTPView, self).__init__()
        self._allow_cross_domain = allow_cross_domain
        self._preflight_response = preflight_response

    @property
    def cross_domain_allowed(self):
        return self._allow_cross_domain

    @property
    def preflight_response(self):
        return self._preflight_response


class BaseTCPView(BaseView):
    '''base class for TCP views'''

    def __init__(self):
        super(BaseTCPView, self).__init__()


class TCPView(BaseTCPView):
    def __init__(self):
        super(TCPView, self).__init__()
