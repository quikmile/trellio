from asyncio import TimeoutError, Future, get_event_loop
from aiohttp.web import Response

from .utils.ordered_class_member import OrderedClassMembers
from .utils.functions import unique_hex


class _Service:
    _PUB_PKT_STR = 'publish'
    _REQ_PKT_STR = 'request'
    _RES_PKT_STR = 'response'

    def __init__(self, service_name, service_version):
        self._service_name = service_name.lower()
        self._service_version = str(service_version)
        self._tcp_bus = None
        self._pubsub_bus = None
        self._http_bus = None

    @property
    def name(self):
        return self._service_name

    @property
    def version(self):
        return self._service_version

    @property
    def properties(self):
        return self.name, self.version

    @staticmethod
    def time_future(future: Future, timeout: int):
        def timer_callback(f):
            if not f.done() and not f.cancelled():
                f.set_exception(TimeoutError())

        get_event_loop().call_later(timeout, timer_callback, future)


class _ServiceHost(_Service):
    def __init__(self, service_name, service_version, host_ip, host_port):
        super(_ServiceHost, self).__init__(service_name, service_version)
        self._node_id = unique_hex()
        self._ip = host_ip
        self._port = host_port
        self._clients = []

    def is_for_me(self, service, version):
        return service == self.name and version == self.version

    @property
    def node_id(self):
        return self._node_id

    @property
    def socket_address(self):
        return self._ip, self._port

    @property
    def host(self):
        return self._ip

    @property
    def port(self):
        return self._port


def default_preflight_response(request):
    headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE',
               'Access-Control-Allow-Headers': 'accept, content-type'}
    return Response(status=200, headers=headers)


class HTTPService(_ServiceHost, metaclass=OrderedClassMembers):
    def __init__(self, service_name, service_version, host_ip=None, host_port=None, ssl_context=None,
                 allow_cross_domain=False,
                 preflight_response=default_preflight_response):
        super(HTTPService, self).__init__(service_name, service_version, host_ip, host_port)
        self._ssl_context = ssl_context
        self._allow_cross_domain = allow_cross_domain
        self._preflight_response = preflight_response

    @property
    def ssl_context(self):
        return self._ssl_context

    @property
    def cross_domain_allowed(self):
        return self._allow_cross_domain

    @property
    def preflight_response(self):
        return self._preflight_response


class HTTPServiceClient(_Service):
    def __init__(self, service_name, service_version):
        super(HTTPServiceClient, self).__init__(service_name, service_version)

    def _send_http_request(self, app_name, method, entity, params):
        response = yield from self._http_bus.send_http_request(app_name, self.name, self.version, method, entity,
                                                               params)
        return response
