# responsible for storage of all config and connections to config clients
import os
import sys
import json
import asyncio
import asyncio.streams
from aiohttp import web
from urllib.request import urlopen


class ConfigHostAdmin:
    def __init__(self, config_host):
        self.admin_http_host = ''  # host addr at which confighost web api will be served
        self.admin_http_port = ''  # port
        self.config_host = config_host

    def get_aiohttp_application(self):
        def handle_client_info(request):
            name = request.match_info.get('name')
            name_dict = {i['service_name']: i for i in self.config_host.CLIENT_CONNECTIONS}
            if name in name_dict:
                return web.Response(text=str(name_dict[name]))  # placeholder

        app = web.Application()
        app.router.add_get('/service/{name}/', handle_client_info)
        return app

    def start(self):
        self.app = self.get_aiohttp_application()
        web.run_app(self.app, host=self.admin_http_host, port=self.admin_http_port)

    def stop(self):
        pass


def config_admin_factory(c_h):
    return ConfigHostAdmin(c_h)


class BaseConfigServer:  # over-ride usecase, creating a centralized config server on a domain using nginx etc.
    '''
    this class does'nt have logic for config management
    '''

    def __init__(self):
        self.__clients = {}

    def _accept_client(self, client_reader, client_writer):
        """
        This method accepts a new config connection
        """
        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_client(client_reader, client_writer))
        self.__clients[task] = (client_reader, client_writer)  # temporary dictionary until validation is done

        def client_done(task):
            self.client_handler_exit()
            del self.__clients[task]

        task.add_done_callback(client_done)

    async def _handle_client(self, client_reader, client_writer):
        data = await client_reader.read().decode("utf-8")
        await self.config_handler(data, client_reader, client_writer)
        # This enables us to have flow control in our connection.
        await client_writer.drain()

    def config_handler(self, data, client_reader, client_writer):  # method where everything is done
        raise NotImplementedError

    def client_exit(self):
        raise NotImplementedError

    def client_handler_exit(self):
        raise NotImplementedError

    def start(self, loop, host, port):
        self.server = loop.run_until_complete(
            asyncio.streams.start_server(self._accept_client,
                                         host, port,
                                         loop=loop))

    def stop(self, loop):
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None


class ConfigHost(BaseConfigServer):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self.loop = asyncio.get_event_loop()
        self.CLIENT_CONNECTIONS = {}
        self.admin = config_admin_factory(self)
        super(ConfigHost, self).___init__(host, port)

    async def config_handler(self, data, client_reader, client_writer):  # main method
        file_path = json.loads(data)
        data = self.get_file_content(file_path['FILE_PATH'])
        client_dict = {}
        client_dict['raw_config'] = data
        client_dict['reader'] = client_reader
        client_dict['writer'] = client_writer
        self.CLIENT_CONNECTIONS[data['UNIQUE_SERVICE_NAME']] = client_dict  # service name will be unique
        await self.start_client(data['UNIQUE_SERVICE_NAME'])  # start the service now

    async def start_client(self, service_name):
        c_d = self.CLIENT_CONNECTIONS[service_name]
        c_d['writer'].write(':start_client')
        await c_d['writer'].drain()

    def get_file_content(self, c_file):
        try:
            # remote file
            data = urlopen(c_file).read()  # blocking, we have to wait for file
            return json.loads(data)
        except:
            # local file
            if os.path.exists(c_file):
                with open(c_file, 'rb') as file:
                    data = file.read()
                    self.data = json.loads(data)
                    return data
            else:
                raise Exception('Invalid file details!!')

    async def update_client_file(self, service_name):  # will be called by web api, cli command etc.,
        # when file is changed successfully
        new_data = self.get_file_content(self.CLIENT_CONNECTIONS[service_name]['FILE_PATH'])
        n_service_name = new_data['UNIQUE_SERVICE_NAME']
        self.CLIENT_CONNECTIONS[n_service_name]['raw_config'] = new_data
        if service_name != n_service_name:
            del self.CLIENT_CONNECTIONS[service_name]

    def start_config(self):
        self.start(self.loop, self._host, self._port)
        if self.admin:
            self.admin.start()

    def stop_config(self):
        if self.admin:
            self.admin.stop()
        self.stop(asyncio.get_event_loop())
