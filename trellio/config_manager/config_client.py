import asyncio
import os
import json
from concurrent.futures import ProcessPoolExecutor
from trellio.host import Host
from urllib.request import urlopen

class ConfigClient:#assign it, at the end of class

    def __init__(self, host_ip, host_port, file_path, service):
        self.host_ip = host_ip
        self.host_port = host_port
        self.config_file = file_path
        self._loop = asyncio.get_event_loop()
        self.service = service


    def export(self):
        self._connect_to_config_host()#creates connection to config host
        f = self.get_file_content()
        self._upload_config(f)#verification and storage


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


    def _connect_to_config_host(self):
        client_reader, client_writer = yield from asyncio.open_connection(self.host_ip,
                                                                      self.host_port)
        self.config_host_reader = client_reader
        self.config_host_writer = client_writer

    def _upload_config(self, json_string):
        self.config_host_writer(json_string)


    def start_and_poll_on_config_host(self):
        def _poll(reader):
            while True:
                data = yield from reader.read()
                if data:
                    self.data = json.loads(data)#keep updating it
                    self._stop()
                    self._run()
        self.export()#blocking
        infinite_future = self._loop.run_in_executor(ProcessPoolExecutor(max_workers=1),
                                                     _poll,
                                                     self.config_host_reader)
        self._run()

    def _run(self):#incomplete
        tcp = self.service(self.data['SERVICE_HOST'], self.data['SERVICE_PORT'])
        Host.configure(self.service.__name__)
        Host.attach_tcp_service(tcp)
        Host.run()


    def _stop(self):
        pass#????
