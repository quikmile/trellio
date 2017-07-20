import asyncio
import logging
import os
import signal
import warnings
from functools import partial

from aiohttp.web import Application

from .bus import TCPBus
from .protocol_factory import get_trellio_protocol
from .pubsub import Publisher, Subscriber
from .registry_client import RegistryClient
from .services import HTTPService, TCPService
from .signals import ServiceReady
from .utils.decorators import deprecated
from .utils.log import setup_logging
from .utils.stats import Stats, Aggregator


class Host:
    """Serves as a static entry point and provides the boilerplate required to host and run a trellio Service.

    Example::

        Host.configure('SampleService')
        Host.attachService(SampleHTTPService())
        Host.run()

    """
    registry_host = None
    registry_port = None
    pubsub_host = None
    pubsub_port = None
    host_name = None
    service_name = None
    http_host = None
    http_port = None
    tcp_host = None
    tcp_port = None
    ssl_context = None
    ronin = False  # If true, the trellio service runs solo without a registry

    _host_id = None
    _tcp_service = None
    _http_service = None
    _publisher = None
    _subscribers = []
    _tcp_views = []
    _http_views = []
    _logger = logging.getLogger(__name__)
    _smtp_handler = None

    @classmethod
    def configure(cls, host_name: str = '', service_name: str = '', service_version='',
                  http_host: str = '127.0.0.1', http_port: int = 8000,
                  tcp_host: str = '127.0.0.1', tcp_port: int = 8001, ssl_context=None,
                  registry_host: str = "0.0.0.0", registry_port: int = 4500,
                  pubsub_host: str = "0.0.0.0", pubsub_port: int = 6379, ronin: bool = False):
        """ A convenience method for providing registry and pubsub(redis) endpoints

        :param host_name: Used for process name
        :param registry_host: IP Address for trellio-registry; default = 0.0.0.0
        :param registry_port: Port for trellio-registry; default = 4500
        :param pubsub_host: IP Address for pubsub component, usually redis; default = 0.0.0.0
        :param pubsub_port: Port for pubsub component; default= 6379
        :return: None
        """
        Host.host_name = host_name
        Host.service_name = service_name
        Host.service_version = str(service_version)
        Host.http_host = http_host
        Host.http_port = http_port
        Host.tcp_host = tcp_host
        Host.tcp_port = tcp_port
        Host.registry_host = registry_host
        Host.registry_port = registry_port
        Host.pubsub_host = pubsub_host
        Host.pubsub_port = pubsub_port
        Host.ssl_context = ssl_context
        Host.ronin = ronin

    @classmethod
    def get_http_service(cls):
        return cls._http_service

    @classmethod
    def get_tcp_service(cls):
        return cls._tcp_service

    @classmethod
    def get_tcp_clients(cls):
        tcp_service = cls.get_tcp_service()
        if tcp_service:
            return tcp_service.clients

    @classmethod
    def get_publisher(cls):
        return cls._publisher

    @classmethod
    def get_subscribers(cls):
        return cls._subscribers

    @classmethod
    def get_tcp_views(cls):
        return cls._tcp_views

    @classmethod
    def get_http_views(cls):
        return cls._http_views

    @classmethod
    @deprecated
    def attach_service(cls, service):
        """ Allows you to attach one TCP and one HTTP service

        deprecated:: 2.1.73 use http and tcp specific methods
        :param service: A trellio TCP or HTTP service that needs to be hosted
        """
        if isinstance(service, HTTPService):
            cls._http_service = service
        elif isinstance(service, TCPService):
            cls._tcp_service = service
        else:
            cls._logger.error('Invalid argument attached as service')
        cls._set_bus(service)

    @classmethod
    def attach_http_service(cls, http_service: HTTPService):
        """ Attaches a service for hosting
        :param http_service: A HTTPService instance
        """
        if cls._http_service is None:
            cls._http_service = http_service
            cls._set_bus(http_service)
        else:
            warnings.warn('HTTP service is already attached')

    @classmethod
    def attach_tcp_service(cls, tcp_service: TCPService):
        """ Attaches a service for hosting
        :param tcp_service: A TCPService instance
        """
        if cls._tcp_service is None:
            cls._tcp_service = tcp_service
            cls._set_bus(tcp_service)
        else:
            warnings.warn('TCP service is already attached')

    @classmethod
    def attach_http_views(cls, http_views: list):
        views_instances = []
        for view_class in http_views:
            instance = view_class()
            instance.host = Host
            views_instances.append(instance)
        cls._http_views.extend(views_instances)

    @classmethod
    def attach_tcp_views(cls, tcp_views: list):
        views_instances = []
        for view_class in tcp_views:
            instance = view_class()
            instance.host = Host
            views_instances.append(instance)
        cls._tcp_views.extend(views_instances)

    @classmethod
    def attach_publisher(cls, publisher: Publisher):
        if cls._publisher is None:
            cls._publisher = publisher
        else:
            warnings.warn('Publisher is already attached')

    @classmethod
    def attach_subscribers(cls, subscribers: list):
        if all([isinstance(subscriber, Subscriber) for subscriber in subscribers]):
            if not cls._subscribers:
                cls._subscribers = subscribers
            else:
                warnings.warn('Subscribers are already attached')

    @classmethod
    def run(cls):
        """ Fires up the event loop and starts serving attached services
        """
        if cls._tcp_service or cls._http_service or cls._http_views or cls._tcp_views:
            cls._set_host_id()
            cls._setup_logging()
            cls._set_process_name()
            cls._set_signal_handlers()
            cls._start_pubsub()
            cls._start_server()
        else:
            cls._logger.error('No services to host')

    @classmethod
    def _set_process_name(cls):
        from setproctitle import setproctitle
        setproctitle('trellio_{}_{}'.format(cls.host_name, cls._host_id))

    @classmethod
    def _stop(cls, signame: str):
        cls._logger.info('\ngot signal {} - exiting'.format(signame))
        asyncio.get_event_loop().stop()

    @classmethod
    def _set_signal_handlers(cls):
        asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGINT'), partial(cls._stop, 'SIGINT'))
        asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGTERM'), partial(cls._stop, 'SIGTERM'))

    @classmethod
    def _create_tcp_server(cls):
        if cls._tcp_service:
            ssl_context = cls._tcp_service.ssl_context
            host_ip, host_port = cls._tcp_service.socket_address
            task = asyncio.get_event_loop().create_server(partial(get_trellio_protocol, cls._tcp_service.tcp_bus),
                                                          host_ip, host_port, ssl=ssl_context)
            result = asyncio.get_event_loop().run_until_complete(task)
            return result

    @classmethod
    def _create_http_server(cls):
        if cls._http_service or cls._http_views:
            host_ip, host_port = cls.http_host, cls.http_port
            ssl_context = cls.ssl_context
            handler = cls._make_aiohttp_handler()
            task = asyncio.get_event_loop().create_server(handler, host_ip, host_port, ssl=ssl_context)
            return asyncio.get_event_loop().run_until_complete(task)

    @classmethod
    def _make_aiohttp_handler(cls):
        app = Application(loop=asyncio.get_event_loop())

        if cls._http_service:
            for each in cls._http_service.__ordered__:
                # iterate all attributes in the service looking for http endpoints and add them
                fn = getattr(cls._http_service, each)
                if callable(fn) and getattr(fn, 'is_http_method', False):
                    for path in fn.paths:
                        app.router.add_route(fn.method, path, fn)
                        if cls._http_service.cross_domain_allowed:
                            # add an 'options' for this specific path to make it CORS friendly
                            app.router.add_route('options', path, cls._http_service.preflight_response)

        for view in cls._http_views:
            for each in view.__ordered__:
                fn = getattr(view, each)
                if callable(fn) and getattr(fn, 'is_http_method', False):
                    for path in fn.paths:
                        app.router.add_route(fn.method, path, fn)
                        if view.cross_domain_allowed:
                            # add an 'options' for this specific path to make it CORS friendly
                            app.router.add_route('options', path, view.preflight_response)

        handler = app.make_handler(access_log=cls._logger)
        return handler

    @classmethod
    def _set_host_id(cls):
        from uuid import uuid4
        cls._host_id = uuid4()

    @classmethod
    def _start_server(cls):
        tcp_server = cls._create_tcp_server()
        http_server = cls._create_http_server()
        if not cls.ronin:
            if cls._tcp_service:
                asyncio.get_event_loop().run_until_complete(cls._tcp_service.tcp_bus.connect())
                # if cls._http_service:
                #     asyncio.get_event_loop().run_until_complete(cls._http_service.tcp_bus.connect())
        if tcp_server:
            cls._logger.info('Serving TCP on {}'.format(tcp_server.sockets[0].getsockname()))
        if http_server:
            cls._logger.info('Serving HTTP on {}'.format(http_server.sockets[0].getsockname()))
        cls._logger.info("Event loop running forever, press CTRL+C to interrupt.")
        cls._logger.info("pid %s: send SIGINT or SIGTERM to exit." % os.getpid())
        cls._logger.info("Triggering ServiceReady signal")
        asyncio.get_event_loop().run_until_complete(ServiceReady._run())
        try:
            asyncio.get_event_loop().run_forever()
        except Exception as e:
            print(e)
        finally:
            if tcp_server:
                tcp_server.close()
                asyncio.get_event_loop().run_until_complete(tcp_server.wait_closed())

            if http_server:
                http_server.close()
                asyncio.get_event_loop().run_until_complete(http_server.wait_closed())

            asyncio.get_event_loop().close()

    @classmethod
    def _start_pubsub(cls):
        if not cls.ronin:
            if cls._publisher:
                asyncio.get_event_loop().run_until_complete(cls._publisher.create_pubsub_handler())

        for subscriber in cls._subscribers:
            asyncio.get_event_loop().run_until_complete(subscriber.create_pubsub_handler())
            asyncio.async(subscriber.register_for_subscription())

    @classmethod
    def _set_bus(cls, service):
        registry_client = RegistryClient(asyncio.get_event_loop(), cls.registry_host, cls.registry_port)
        tcp_bus = TCPBus(registry_client)
        registry_client.conn_handler = tcp_bus
        # pubsub_bus = PubSubBus(cls.pubsub_host, cls.pubsub_port, registry_client)  # , cls._tcp_service._ssl_context)
        registry_client.bus = tcp_bus
        if isinstance(service, TCPService):
            tcp_bus.tcp_host = service
        if isinstance(service, HTTPService):
            tcp_bus.http_host = service
        service.tcp_bus = tcp_bus
        # service.pubsub_bus = pubsub_bus

    @classmethod
    def _setup_logging(cls):
        identifier = '{}'.format(cls.service_name)
        setup_logging(identifier)
        if cls._smtp_handler:
            logger = logging.getLogger()
            logger.addHandler(cls._smtp_handler)
        Stats.service_name = cls.service_name
        Aggregator._service_name = cls.service_name
        Aggregator.periodic_aggregated_stats_logger()
