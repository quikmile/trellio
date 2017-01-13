import json
import importlib

class InvalidConfigurationError(Exception):
    pass

class ConfigHandler:

    middleware_key = 'MIDDLEWARES'
    signal_key = 'SIGNALS'
    http_service_key = 'HTTP_SERVICE'
    tcp_service_key = 'TCP_SERVICE'
    service_name_key = 'SERVICE_NAME'
    host_name = 'HOST_NAME'
    http_version_key = 'HTTP_VERSION'
    version_key = "VERSION"
    reg_host_key = "REGISTRY_HOST"
    reg_port_key = "REGISTRY_PORT"
    redis_host_key = "REDIS_HOST"
    redis_port_key = "REDIS_PORT"
    host_key = "HOST"
    http_host_key = "HTTP_HOST"
    tcp_host_key = "TCP_HOST"
    http_port_key = "HTTP_PORT"
    tcp_port_key = "TCP_PORT"

    def __init__(self, host_class):
        self.settings = None
        self.host = host_class

    @property
    def service_name(self):
        return self.settings[self.service_name_key]


    def set_config(self):
        config_file = 'config.json'
        settings = None
        with open(config_file) as f:
            settings = json.load(f)

        self.settings = settings

    def get_http_service(self):
        http_service = self.settings[self.http_service_key]
        module, class_value = self.import_class_from_path(http_service)
        return class_value

    def get_tcp_service(self):
        http_service = self.settings[self.tcp_service_key]
        module, class_value = self.import_class_from_path(http_service)
        return class_value

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


