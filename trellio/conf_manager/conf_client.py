import os
import copy
import json
import importlib

GLOBAL_CONFIG = {
  "HOST_NAME": "",
  "SERVICE_NAME": "",
  "TCP_VERSION": "",
  "HTTP_VERSION": "",
  "VERSION": '',
  "REGISTRY_HOST": "",
  "REGISTRY_PORT": '',
  "REDIS_HOST": "",
  "REDIS_PORT": '',
  "HTTP_HOST": "",
  "TCP_HOST": "",
  "HTTP_PORT": '',
  "TCP_PORT": '',
  "MIDDLEWARES": None,
  "SIGNALS": None,
  "TCP_CLIENTS": None,
  "HTTP_CLIENTS": None,
  # "SERVICE_PATH": "",
  "DATABASE_SETTINGS": {
    "database": "",
    "user": "",
    "password": "",
    "host": "",
    "port": ''
  }
}

class InvalidConfigurationError(Exception):
    pass

class ConfigHandler:

    middleware_key = 'MIDDLEWARES'
    signal_key = 'SIGNALS'
    service_name_key = 'SERVICE_NAME'
    host_name = 'HOST_NAME'
    http_version_key = 'HTTP_VERSION'
    tcp_version_key = 'TCP_VERSION'
    version_key = "VERSION"
    reg_host_key = "REGISTRY_HOST"
    reg_port_key = "REGISTRY_PORT"
    redis_host_key = "REDIS_HOST"
    redis_port_key = "REDIS_PORT"
    http_host_key = "HTTP_HOST"
    tcp_host_key = "TCP_HOST"
    http_port_key = "HTTP_PORT"
    tcp_port_key = "TCP_PORT"
    tcp_clients_key = "TCP_CLIENTS"
    http_clients_key = "HTTP_CLIENTS"
    database_key = 'DATABASE_SETTINGS'
    # service_path_key = "SERVICE_PATH"

    def __init__(self, host_class, service_path):
        self.service_path = service_path
        self.settings = None
        self.host = host_class

    def setup(self):
        if self.settings:
            self.find_services()
        else:
            raise InvalidConfigurationError('call set_config before!!')


    def find_services(self):
        service_path = self.service_path
        if not service_path:
            service_path = os.path.abspath('service.py')
        self.service_module = importlib.import_module(service_path)

    @property
    def service_name(self):
        return self.settings[self.service_name_key]

    def get_tcp_clients(self):
        clients = []
        tcp_client_paths = self.settings[self.tcp_clients_key]
        for i in tcp_client_paths:
            module, cur_client = self.import_class_from_path(i)
            clients.append(cur_client)
        return clients

    def get_http_clients(self):
        clients = []
        http_client_paths = self.settings[self.http_clients_key]
        for i in http_client_paths:
            module, cur_client = self.import_class_from_path(i)
            clients.append(cur_client)
        return clients

    def setup_host(self):
        host = self.host
        http_service = self.get_http_service()
        tcp_service = self.get_tcp_service()
        tcp_clients = self.get_tcp_clients()
        http_clients = self.get_http_clients()
        host.registry_host = self.settings[self.reg_host_key]
        host.registry_port = self.settings[self.reg_port_key]
        host.pubsub_host = self.settings[self.redis_host_key]
        host.pubsub_port = self.settings[self.redis_port_key]
        host.ronin = True#todo only for testing
        host.name = self.settings[self.host_name]
        http_service.clients = [i() for i in http_clients]
        tcp_service.clients = [i() for i in tcp_clients]
        host.attach_service(http_service)
        host.attach_service(tcp_service)

    def get_database_settings(self):
        return self.settings[self.database_key]

    def set_config(self, config_path):
        settings = None
        with open(config_path) as f:
            settings = json.load(f)
        new_settings = copy.deepcopy(GLOBAL_CONFIG)
        new_settings.update(settings)
        self.settings = new_settings

    def get_http_service(self):
        from trellio.services import HTTPService
        service_sub_class = HTTPService.__subclasses__()[0]
        http_service = service_sub_class(self.settings[self.service_name_key],
                                         self.settings[self.http_version_key],
                                         self.settings[self.http_host_key],
                                         self.settings[self.http_port_key])
        return http_service

    def get_tcp_service(self):
        from trellio.services import TCPService
        service_sub_class = TCPService.__subclasses__()[0]
        tcp_service = service_sub_class(self.settings[self.service_name_key],
                                         self.settings[self.tcp_version_key],
                                         self.settings[self.tcp_host_key],
                                         self.settings[self.tcp_port_key])
        return tcp_service

    def import_class_from_path(self, path):
        broken = path.split('.')
        class_name = broken[-1]
        module_name = '.'.join(broken[:-1])
        module = importlib.import_module(module_name)
        class_value = getattr(module, class_name)
        return module, class_value


    def enable_middlewares(self):
        middlewares = self.settings[self.middleware_key]
        http_service = self.host.get_http_service()
        middle_cls = []
        for i in middlewares:
            module, class_value = self.import_class_from_path(i)
            if not class_value:
                raise InvalidConfigurationError
            else:
                middle_cls.append(class_value())
        http_service.http_middlewares = middle_cls


    def enable_signals(self):
        '''
        e.g signal_dict = {signal_path:signal_receiver_path_list, ....}
        :return:
        '''
        signal_dict = self.settings[self.signal_key]
        for i in signal_dict.keys():
            sig_module, signal_class = self.import_class_from_path(i)
            for j in signal_dict[i]:
                recv_module, recv_coro = self.import_class_from_path(j)
                signal_class.register(recv_coro)#registering reciever




