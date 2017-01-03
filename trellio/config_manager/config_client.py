import asyncio
import os
import json
from concurrent.futures import ProcessPoolExecutor
from trellio.host import Host
from urllib.request import urlopen
import hashlib

class ConfigClient:#assign it, at the end of class

    def __init__(self, host_ip, host_port, file_path, h_service, t_service):
        self.host_ip = host_ip
        self.host_port = host_port
        self.config_file = file_path
        self._loop = asyncio.get_event_loop()
        self.http_service = h_service
        self.tcp_service = t_service
        self.config_host_reader = None
        self.config_host_writer = None
        self.running = False
        self._run_lock1 = asyncio.Lock()
        self._run_lock2 = asyncio.Lock()
        self.data = {}

    def start_config(self):
        self.export_to_host()

    def export_to_host(self):
        yield self._connect_to_config_host()#creates connection to config host
        d = {'FILE_PATH': self.config_file}
        self._upload(json.dumps(d))#upload the file path to config host


    def get_file_content(self):
        try:
            #remote file
            data = urlopen(self.config_file).read()#blocking, we have to wait for file
            return json.loads(data)
        except:
            #local file
            if os.path.exists(self.config_file):
                with open(self.config_file, 'rb') as file:
                    data = file.read()
                    self.data = json.loads(data)
                    return data
            else:
                raise Exception('Invalid file details!!')


    async def _connect_to_config_host(self):
        if not(self.config_host_reader or self.config_host_writer):
            client_reader, client_writer = await asyncio.open_connection(self.host_ip,
                                                                      self.host_port)
            self.config_host_reader = client_reader
            self.config_host_writer = client_writer

    def _upload(self, json_string):
        self.config_host_writer.write(json_string)
        yield from self.config_host_writer.drain()


    def handle_request(self, req_str):
        if req_str == ':start_service':
            self.restart()

    def config_handler(self):#poll on file and config host will directly change the file
        def _poll(reader):
            while True:#optimize
                data = yield from reader.read()
                if data:
                    self.handle_request(data)
                else:
                    yield from asyncio.sleep(1)

        file_hash = hashlib.md5(self.get_file_content()).hexdigest()

        def _poll_on_file():
            while True:
                if file_hash != hashlib.md5(self.get_file_content()).hexdigest():
                    self.restart()
                else:
                    yield from asyncio.sleep()

        infinite_future1 = self._loop.run_in_executor(ProcessPoolExecutor(max_workers=1),
                                                     _poll,
                                                     self.config_host_reader)
        infinite_future2 = self._loop.run_in_executor(ProcessPoolExecutor(max_workers=1),
                                                     _poll_on_file)

    def restart(self):
        with (yield from self._run_lock1):
            self._stop()
            self.running = False
        with (yield from self._run_lock2):
            self._run()
            self.running = True

    def _run(self):#incomplete
        '''
        {
          "HTTP_SERVICE_HOST": "",
          "HTTP_SERVICE_PORT": "",
          "TCP_SERVICE_HOST": "",
          "TCP_SERVICE_PORT": "",
          "REGISTRY_HOST": "",
          "REGISTRY_PORT": "",
          "UNIQUE_SERVICE_NAME": "",
          "PUBSUB_H0ST": "",
          "PUBSUB_PORT": ""
        }
        :return:
        '''
        if not self.data:
            self.data = self.get_file_content()

        Host.name = self.data['UNIQUE_SERVICE_NAME']
        if self.tcp_service:
            tcp = self.tcp_service(self.data['TCP_SERVICE_HOST'], self.data['TCP_SERVICE_PORT'])
            Host.attach_tcp_service(tcp)
        if self.http_service:
            http = self.http_service(self.data['HTTP_SERVICE_HOST'], self.data['HTTP_SERVICE_PORT'])
            Host.attach_http_service(http)
        Host.registry_host = self.data['REGISTRY_HOST']
        Host.registry_port = self.data['REGISTRY_PORT']
        Host.pubsub_host = self.data['PUBSUB_HOST']
        Host.pubsub_port = self.data['PUBSUB_PORT']
        Host.run()

    def _stop(self):
        asyncio.get_event_loop().stop()
