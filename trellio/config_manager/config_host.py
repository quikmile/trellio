#responsible for storage of all config and connections to config clients
import sys
import asyncio
import asyncio.streams


class BaseConfigServer:#over-ride usecase, creating a centralized config server on a domain using nginx etc.

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
        self._host = host
        self._port = port
        self.CLIENT_CONNECTIONS = {}

    await def config_handler(self, data, client_reader, client_writer):
        #todo
        self.CLIENT_CONNECTIONS['service_name'] = (client_reader, client_writer)

