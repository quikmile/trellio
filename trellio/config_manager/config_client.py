import asyncio
import urllib2
import os
import json
from concurrent.futures import ProcessPoolExecutor
from trellio.host import Host

class ConfigClient:#assign it at the end of class

    def __init__(self, host_ip, host_port, file_path, file_name, service):
        self.host_ip = host_ip
        self.host_port = host_port
        self.config_file = file_path
        self.file_name = file_name
        self._loop = asyncio.get_event_loop()
        self.service = service


    def export(self):
        self._connect_to_config_host()#creates connection to config host
        f = self.get_file_content()
        self._upload_config(f)#verification and storage


    def get_file_content(self):
        try:
            urllib2.urlopen(self.config_file, filename=self.file_name)
        except:
            pass#no a url

        if os.path.exists(self.config_file):
            with open(self.file_name, 'rb') as file:
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
        client_writer.write()

    def _upload_config(self, json_string):
        self.config_host_writer(json_string)


    def start_and_poll_on_config_host(self):
        def _poll(reader):
            while True:
                data = yield from reader.read()
                self.data = json.loads(data)#keep updating it
                self._stop()
                self._run()
                #How to re-run?

        infinite_future = self._loop.run_in_executor(ProcessPoolExecutor(max_workers=1), _poll, self.config_host_reader)
        self._run()

    def _run(self):#incomplete
        tcp = self.service(self.data['SERVICE_HOST'], self.data['SERVICE_PORT'])
        Host.configure(self.service.__name__)
        Host.attach_tcp_service(tcp)
        Host.run()


    def _stop(self):
        pass#????