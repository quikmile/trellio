import asyncio
import faulthandler
import logging
import multiprocessing
import os
import signal
import socket
import warnings
from functools import partial

import uvloop
from aiohttp.web import Application
from japronto.protocol.creaper import Reaper

from .bus import TCPBus
from .protocol_factory import get_trellio_protocol
from .pubsub import Publisher, Subscriber
from .registry_client import RegistryClient
from .services import HTTPService, TCPService
from .signals import ServiceReady
from .utils.decorators import deprecated
from .utils.log import setup_logging
from .utils.stats import Stats, Aggregator

signames = {int(v): v.name for k, v in signal.__dict__.items() if isinstance(v, signal.Signals)}


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
    debug = False
    num_workers = 1

    _host_id = None
    _tcp_service = None
    _http_service = None
    _publisher = None
    _subscribers = []
    _tcp_views = []
    _http_views = []
    _logger = None
    _smtp_handler = None
    _workers = set()
    _reaper = None
    _reaper_settings = {}
    _loop = uvloop.new_event_loop()
    _connections = set()

    @classmethod
    def configure(cls, host_name: str = '', service_name: str = '', service_version='',
                  http_host: str = '127.0.0.1', http_port: int = 8000,
                  tcp_host: str = '127.0.0.1', tcp_port: int = 8001, ssl_context=None,
                  registry_host: str = "0.0.0.0", registry_port: int = 4500,
                  pubsub_host: str = "0.0.0.0", pubsub_port: int = 6379, ronin: bool = False,
                  workers: int = 1, debug: bool = False):
        """ A convenience method for providing registry and pubsub(redis) endpoints

        :param host_name: Used for process name
        :param registry_host: IP Address for trellio-registry; default = 0.0.0.0
        :param registry_port: Port for trellio-registry; default = 4500
        :param pubsub_host: IP Address for pubsub component, usually redis; default = 0.0.0.0
        :param pubsub_port: Port for pubsub component; default= 6379
        :return: None
        """

        if host_name:
            Host.host_name = host_name
        else:
            Host.host_name = service_name
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
        Host.debug = debug
        Host.num_workers = workers
        Host._reaper = Reaper(cls, **cls._reaper_settings)

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
            # cls._set_host_id()
            # cls._setup_logging()
            # cls._set_signal_handlers()
            # cls._start_pubsub()
            cls._start_server()
        else:
            cls._logger.error('No services to host')

    @classmethod
    def _set_process_name(cls, worker=1):
        from setproctitle import setproctitle
        setproctitle('trellio_{}-{}'.format(cls.host_name, worker))

    @classmethod
    def _stop(cls, signame: str):
        cls._logger.info('\ngot signal {} - exiting'.format(signame))
        asyncio.get_event_loop().stop()
        for worker in cls._workers:
            worker.terminate()

    @classmethod
    def _set_signal_handlers(cls):
        asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGINT'), partial(cls._stop, 'SIGINT'))
        asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGTERM'), partial(cls._stop, 'SIGTERM'))

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
    def _create_tcp_server(cls, sock):
        if cls._tcp_service:
            ssl_context = cls._tcp_service.ssl_context
            task = asyncio.get_event_loop().create_server(partial(get_trellio_protocol, cls._tcp_service.tcp_bus),
                                                          sock=sock, ssl=ssl_context)
            return asyncio.get_event_loop().run_until_complete(task)

    @classmethod
    def _create_http_server(cls, sock):
        if cls._http_service or cls._http_views:
            ssl_context = cls.ssl_context
            handler = cls._make_aiohttp_handler()
            task = asyncio.get_event_loop().create_server(handler, sock=sock, ssl=ssl_context)
            return asyncio.get_event_loop().run_until_complete(task)

    @classmethod
    def _create_server(cls, http_sock=None, tcp_sock=None, worker=None):
        faulthandler.enable()

        cls._logger = logging.getLogger(__name__)
        # cls._set_host_id()
        cls._set_process_name(worker)
        cls._setup_logging(worker)

        cls._start_pubsub()

        tcp_server = cls._create_tcp_server(tcp_sock)
        http_server = cls._create_http_server(http_sock)

        if tcp_server:
            if not cls.ronin:
                asyncio.get_event_loop().run_until_complete(cls._tcp_service.tcp_bus.connect())

        if http_server:
            cls._logger.info('Serving HTTP on {}'.format(http_server.sockets[0].getsockname()))

        asyncio.get_event_loop().run_until_complete(ServiceReady._run())

        cls._logger.info("Event loop running forever, press CTRL+C to interrupt.")
        cls._logger.info("pid %s: send SIGINT or SIGTERM to exit." % os.getpid())
        cls._logger.info("Triggering ServiceReady signal")

        cls._set_signal_handlers()

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

            asyncio.get_event_loop().run_until_complete(cls.drain())
            cls._reaper.stop()
            asyncio.get_event_loop().close()

    @classmethod
    def _create_sock(cls, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        os.set_inheritable(sock.fileno(), True)

        return sock

    @classmethod
    def _start_workers(cls, worker_num, target, http_sock, tcp_sock):
        for i in range(worker_num or 1):
            worker = multiprocessing.Process(
                target=target,
                kwargs=dict(http_sock=http_sock, tcp_sock=tcp_sock, worker=i + 1))
            worker.daemon = True
            worker.start()
            cls._workers.add(worker)

    @classmethod
    def _join_workers(cls):
        for worker in cls._workers:
            worker.join()

            if worker.exitcode > 0:
                print('Worker exited with code {}'.format(worker.exitcode))
            elif worker.exitcode < 0:
                try:
                    signame = signames[-worker.exitcode]
                except KeyError:
                    print(
                        'Worker crashed with unknown code {}!'
                            .format(worker.exitcode))
                else:
                    print('Worker crashed on signal {}!'.format(signame))

    @classmethod
    def _start_server(cls):
        tcp_sock = cls._create_sock(cls.tcp_host, cls.tcp_port)
        http_sock = cls._create_sock(cls.http_host, cls.http_port)

        cls._start_workers(cls.num_workers, cls._create_server, http_sock, tcp_sock)

        tcp_sock.close()
        http_sock.close()

        cls._join_workers()

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
    def _setup_logging(cls, worker):
        identifier = '{}-{}'.format(cls.service_name, worker)
        setup_logging(identifier)
        if cls._smtp_handler:
            logger = logging.getLogger()
            logger.addHandler(cls._smtp_handler)
        Stats.service_name = cls.service_name
        Aggregator._service_name = cls.service_name
        Aggregator.periodic_aggregated_stats_logger()

    @classmethod
    def _get_idle_and_busy_connections(cls):
        # FIXME if there is buffered data in gather the connections should be
        # considered busy, now it's idle
        return [c for c in cls._connections if c.pipeline_empty], [c for c in cls._connections if not c.pipeline_empty]

    @classmethod
    async def drain(cls):
        # TODO idle connections will close connection with half-read requests
        idle, busy = cls._get_idle_and_busy_connections()
        for c in idle:
            c.transport.close()
        # for c in busy_connections:
        #            need to implement something that makes protocol.on_data
        #            start rejecting incoming data
        #            this closes transport unfortunately
        #            sock = c.transport.get_extra_info('socket')
        #            sock.shutdown(socket.SHUT_RD)

        if idle or busy:
            print('Draining connections...')
        else:
            return

        if idle:
            print('{} idle connections closed immediately'.format(len(idle)))
        if busy:
            print('{} connections busy, read-end closed'.format(len(busy)))

        for x in range(5, 0, -1):
            await asyncio.sleep(1)
            idle, busy = cls._get_idle_and_busy_connections()
            for c in idle:
                c.transport.close()
            if not busy:
                break
            else:
                print(
                    "{} seconds remaining, {} connections still busy"
                        .format(x, len(busy)))

        _, busy = cls._get_idle_and_busy_connections()
        if busy:
            print('Forcefully killing {} connections'.format(len(busy)))
        for c in busy:
            c.pipeline_cancel()
