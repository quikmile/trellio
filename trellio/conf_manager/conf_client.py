import copy
import importlib
import json
import os

GLOBAL_CONFIG = {
    "RONIN": False,
    "HOST_NAME": "",
    "SERVICE_NAME": "",
    "SERVICE_VERSION": "",
    "REGISTRY_HOST": "",
    "REGISTRY_PORT": '',
    "REDIS_HOST": "",
    "REDIS_PORT": '',
    "HTTP_HOST": "",
    "TCP_HOST": "",
    "HTTP_PORT": "",
    "TCP_PORT": "",
    "SIGNALS": {},
    "MIDDLEWARES": {},
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
    service_version_key = 'SERVICE_VERSION'
    reg_host_key = "REGISTRY_HOST"
    reg_port_key = "REGISTRY_PORT"
    redis_host_key = "REDIS_HOST"
    redis_port_key = "REDIS_PORT"
    http_host_key = "HTTP_HOST"
    tcp_host_key = "TCP_HOST"
    http_port_key = "HTTP_PORT"
    tcp_port_key = "TCP_PORT"
    database_key = 'DATABASE_SETTINGS'
    ronin_key = "RONIN"

    # service_path_key = "SERVICE_PATH"

    def __init__(self, host_class):
        self.settings = None
        self.host = host_class

    @property
    def service_name(self):
        return self.settings[self.service_name_key]

    def get_tcp_clients(self):
        from trellio.services import TCPServiceClient
        tcp_clients = TCPServiceClient.__subclasses__()
        return tcp_clients

    def get_http_clients(self):
        from trellio.services import HTTPServiceClient
        http_clients = HTTPServiceClient.__subclasses__()
        return http_clients

    def setup_host(self):
        host = self.host
        http_service = self.get_http_service()
        tcp_service = self.get_tcp_service()
        tcp_clients = self.get_tcp_clients()
        http_clients = self.get_http_clients()
        self.enable_middlewares(http_service)
        self.enable_signals()
        host.registry_host = self.settings[self.reg_host_key]
        host.registry_port = self.settings[self.reg_port_key]
        host.pubsub_host = self.settings[self.redis_host_key]
        host.pubsub_port = self.settings[self.redis_port_key]
        host.ronin = self.settings[self.ronin_key]
        host.name = self.settings[self.host_name]
        http_service.clients = [i() for i in http_clients + tcp_clients]
        tcp_service.clients = http_service.clients
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
        parent_dir = os.getcwd().split('/')[-1]
        client_path = parent_dir + '.clients'
        service_path1 = parent_dir + '.service'
        service_path2 = parent_dir + '.services'
        try:
            try:
                importlib.import_module(client_path)
            except:
                pass
            try:
                importlib.import_module(service_path1)
            except:
                pass
            importlib.import_module(service_path2)
        except:
            pass

    def get_http_service(self):
        from trellio.services import HTTPService
        service_sub_class = HTTPService.__subclasses__()[0]
        http_service = service_sub_class(self.settings[self.service_name_key],
                                         self.settings[self.service_version_key],
                                         self.settings[self.http_host_key],
                                         self.settings[self.http_port_key])
        return http_service

    def get_tcp_service(self):
        from trellio.services import TCPService
        service_sub_class = TCPService.__subclasses__()[0]
        tcp_service = service_sub_class(self.settings[self.service_name_key],
                                        self.settings[self.service_version_key],
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

    def enable_middlewares(self, http_service):
        middlewares = self.settings[self.middleware_key] or []
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
        signal_dict = self.settings[self.signal_key] or {}
        for i in signal_dict.keys():
            sig_module, signal_class = self.import_class_from_path(i)
            for j in signal_dict[i]:
                recv_module, recv_coro = self.import_class_from_path(j)
                signal_class.register(recv_coro)  # registering reciever