# responsible for storage of all config and connections to config clients
import asyncio
import asyncio.streams
import json
import os

from aiohttp import web


class ConfigHostAdmin:
    def __init__(self, config_host):
        self.admin_http_host = ''
        self.admin_http_port = ''
        self.config_host = config_host

    def get_aiohttp_application(self):
        def handle_client_info(request):
            name = request.match_info.get('name')
            name_dict = {i['service_name']: i for i in self.config_host.CLIENT_CONNECTIONS}
            if name in name_dict:
                return web.Response(text=str(name_dict[name]))  # placeholder

        app = web.Application()
        app.router.add_get('/service/{name}/', handle_client_info)

    def start(self):
        self.app = self.get_aiohttp_application()
        web.run_app(self.app, host=self.admin_http_host, port=self.admin_http_port)


def config_admin_factory(c_h):
    return ConfigHostAdmin(c_h)


class BaseConfigServer:  # over-ride usecase, creating a centralized config server on a domain using nginx etc.

    def __init__(self):
        self.clients = {}

    def _accept_client(self, client_reader, client_writer):
        """
        This method accepts a new config connection
        """
        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_client(client_reader, client_writer))
        self.clients[task] = (client_reader, client_writer)

        def client_done(task):
            self.client_handler_exit()
            del self.clients[task]

        task.add_done_callback(client_done)

    async def _handle_client(self, client_reader, client_writer):
        data = await client_reader.readline().decode("utf-8")
        await self.config_handler(data, client_reader, client_writer)
        # This enables us to have flow control in our connection.
        await client_writer.drain()

    def config_handler(self, data, client_reader, client_writer):
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
        super(ConfigHost).__init__()
        self._host = host
        self._port = port
        self.loop = asyncio.get_event_loop()
        self.CLIENT_CONNECTIONS = {}
        self.admin = config_admin_factory(self)

    def config_handler(self, data, client_reader, client_writer):
        data = json.loads(data)
        client_dict = {}
        client_dict['raw_config'] = data
        client_dict['reader'] = client_reader
        client_dict['writer'] = client_writer
        self.CLIENT_CONNECTIONS[data['FILE_PATH']] = client_dict

    def get_file_content(self, c_file, c_file_name=''):
        # try: #todo use requests lib instead of urllib2
        #     if not c_file_name:
        #         c_file_name = os.path.basename(c_file)
        #     return urllib2.urlopen(c_file, filename=c_file_name).read()  # blocking, we have to wait for file
        # except:
        #     pass  # no a url

        if os.path.exists(c_file):
            with open(c_file, 'rb') as file:
                data = file.read()
                self.data = json.loads(data)
                return data
        else:
            raise Exception('Invalid file details!!')

    async def update_client(self, service_name):
        name_dict = {i['service_name']: i for i in
                     self.config_host.CLIENT_CONNECTIONS}  # todo self.config_host is undefined
        new_data = self.get_file_content(name_dict[service_name]['FILE_PATH'])
        self.CLIENT_CONNECTIONS[name_dict[service_name]['FILE_PATH']]['raw_config'] = new_data
        writer = self.CLIENT_CONNECTIONS[name_dict[service_name]['FILE_PATH']]['writer']
        await writer.write(json.dumps(new_data))

    def start_hosting(self):
        self.start(self.loop, self._host, self._port)
        self.admin.start()

    def stop(self):  # todo fix this method ??
        self.admin.stop()
        self.stop()
