from functools import partial
from os import getpid

import asyncio
import logging
import signal
from aiohttp import web
from uuid import uuid4


class Host:
    _logger = logging.getLogger(__name__)
    _http_service = None
    _tcp_service = None

    _host_name = None
    _host_id = None

    @classmethod
    def run(cls):
        if cls._tcp_service or cls._http_service:
            cls._set_host_id()
            # cls._setup_logging()
            cls._set_process_name()
            cls._set_signal_handlers()
            cls._start_server()
        else:
            cls._logger.error('No services to host')

    @classmethod
    def _start_server(cls):
        http_server = cls._create_http_server()
        if http_server:
            cls._logger.info('Serving HTTP on {}'.format(http_server.sockets[0].getsockname()))
        cls._logger.info("Event loop running forever, press CTRL+c to interrupt.")
        cls._logger.info("pid %s: send SIGINT or SIGTERM to exit." % getpid())

        try:
            asyncio.get_event_loop().run_forever()
        except Exception as e:
            print(e)
        finally:
            if http_server:
                http_server.close()
                asyncio.get_event_loop().run_until_complete(http_server.wait_closed())

            asyncio.get_event_loop().close()

    @classmethod
    def _create_http_server(cls):
        if cls._http_service:
            handler = cls._make_http_handler()
            task = asyncio.get_event_loop().create_server(handler,
                                                          host=cls._http_service.host,
                                                          port=cls._http_service.port,
                                                          ssl=cls._http_service.ssl_context)
            return asyncio.get_event_loop().run_until_complete(task)

    @classmethod
    def _make_http_handler(cls):
        app = web.Application()
        for each in cls._http_service.routes:
            app.router.add_route(each.method, each.path, each.view)
            if cls._http_service.cross_domain_allowed:
                app.router.add_route('options', each.path, cls._http_service.preflight_response)
        handler = app.make_handler(access_log=cls._logger)
        return handler

    @classmethod
    def _set_process_name(cls):
        setproctitle('trellio_{}_{}'.format(cls._host_name, cls._host_id))

    @classmethod
    def _stop(cls, signame: str):
        cls._logger.info('\ngot signal {} - exiting'.format(signame))
        asyncio.get_event_loop().stop()

    @classmethod
    def _set_signal_handlers(cls):
        asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGINT'), partial(cls._stop, 'SIGINT'))
        asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGTERM'), partial(cls._stop, 'SIGTERM'))

    @classmethod
    def _set_host_id(cls):
        cls._host_id = uuid4()
