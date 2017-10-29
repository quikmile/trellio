import copy
import importlib
import json
import logging
import os

from trellio.services import TCPService, HTTPService
from ..utils.log_handlers import BufferingSMTPHandler

logger = logging.getLogger(__name__)

GLOBAL_CONFIG = {
    "RONIN": False,
    "HOST_NAME": "",
    "ADMIN_EMAILS": [],
    "SERVICE_NAME": "",
    "SERVICE_VERSION": "",
    "REGISTRY_HOST": "",
    "REGISTRY_PORT": "",
    "REDIS_HOST": "",
    "REDIS_PORT": "",
    "HTTP_HOST": "",
    "TCP_HOST": "",
    "HTTP_PORT": "",
    "TCP_PORT": "",
    "SIGNALS": {},
    "MIDDLEWARES": [],
    "APPS": [],
    "DATABASE_SETTINGS": {
        "database": "",
        "user": "",
        "password": "",
        "host": "",
        "port": ""
    },
    "SMTP_SETTINGS": {}
}


class InvalidConfigurationError(Exception):
    pass


class ConfigHandler:
    smtp_host = 'SMTP_HOST'
    smtp_user = 'SMTP_USER'
    smtp_port = 'SMTP_PORT'
    smtp_password = 'SMTP_PASSWORD'
    admin_emails = 'ADMIN_EMAILS'
    middleware_key = 'MIDDLEWARES'
    signal_key = 'SIGNALS'
    service_name_key = 'SERVICE_NAME'
    host_name_key = 'HOST_NAME'
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
    smtp_key = 'SMTP_SETTINGS'
    apps_key = 'APPS'

    # service_path_key = "SERVICE_PATH"

    def __init__(self, host_class):
        self.settings = None
        self.host = host_class

    @property
    def service_name(self):
        return self.settings[self.service_name_key]

    def get_tcp_clients(self):
        from trellio.services import TCPServiceClient
        tcp_clients = self.inheritors(TCPServiceClient)
        return tcp_clients

    def get_http_clients(self):
        from trellio.services import HTTPServiceClient
        http_clients = self.inheritors(HTTPServiceClient)
        return http_clients

    def get_subscribers(self):
        from trellio.pubsub import Subscriber
        subscriber_classes = self.inheritors(Subscriber)
        subscribers = []
        for subs in subscriber_classes:
            s = subs()
            s.pubsub_host = self.settings[self.redis_host_key]
            s.pubsub_port = self.settings[self.redis_port_key]
            subscribers.append(s)
        return subscribers

    def configure_host(self, host):
        host.configure(
            host_name=self.settings[self.host_name_key],
            service_name=self.settings[self.service_name_key],
            service_version=self.settings[self.service_version_key],
            http_host=self.settings[self.http_host_key],
            http_port=self.settings[self.http_port_key],
            tcp_host=self.settings[self.tcp_host_key],
            tcp_port=self.settings[self.tcp_port_key],
            registry_host=self.settings[self.reg_host_key],
            registry_port=self.settings[self.reg_port_key],
            pubsub_host=self.settings[self.redis_host_key],
            pubsub_port=self.settings[self.reg_port_key],
            ronin=self.settings[self.ronin_key]
        )

    def setup_host(self):
        host = self.host
        self.configure_host(host)
        publisher = self.get_publisher()
        subscribers = self.get_subscribers()
        if publisher:
            host.attach_publisher(publisher)
        if subscribers:
            host.attach_subscribers(subscribers)

        http_service = self.get_http_service()
        tcp_service = self.get_tcp_service()
        tcp_clients = self.get_tcp_clients()
        http_clients = self.get_http_clients()
        http_views = self.get_http_views()
        tcp_views = self.get_tcp_views()

        if not http_service:
            http_service = HTTPService(host.service_name, host.service_version, host.http_host, host.http_port)

        if not tcp_service:
            tcp_service = TCPService(host.service_name, host.service_version, host.tcp_host, host.tcp_port)

        self.enable_signals()
        self.enable_middlewares(http_service=http_service, http_views=http_views)

        if http_service:
            # self.register_http_views(http_service)
            host.attach_service(http_service)
            http_service.clients = [i() for i in http_clients + tcp_clients]
            # self.register_tcp_views(tcp_service)

        host.attach_service(tcp_service)

        if http_service:
            tcp_service.clients = http_service.clients

        if http_views:
            host.attach_http_views(http_views)
            for view_inst in host.get_tcp_views():
                pass

        if tcp_views:
            host.attach_tcp_views(tcp_views)
            _tcp_service = host.get_tcp_service()
            _tcp_service.tcp_views = host._tcp_views

        host._smtp_handler = self.get_smtp_logging_handler()

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
        service_path = parent_dir + '.service'

        try:
            importlib.import_module(client_path)
        except:
            logger.warning('No clients found')

        service_imported = True
        service_exception = None
        try:
            importlib.import_module(service_path)
        except Exception as e:
            service_imported = False
            service_exception = e.__traceback__

        if self.settings.get(self.apps_key):
            apps = self.settings[self.apps_key]
            for app in apps:
                views_path = parent_dir + '.{}.views'.format(app)
                try:
                    importlib.import_module(views_path)
                except Exception as e:
                    print(e.__traceback__.__str__())
        else:
            if not service_imported:
                print(service_exception.__str__())

    def get_smtp_logging_handler(self):
        if self.settings.get(self.smtp_key):
            keys = ["smtp_host", "smtp_port", "smtp_user", "smtp_password"]
            setting_keys = self.settings[self.smtp_key].keys()
            missing_keys = list(filter(lambda x: x not in setting_keys, keys))
            if not missing_keys:
                handler = BufferingSMTPHandler(mailhost=self.settings[self.smtp_key]['smtp_host'],
                                               mailport=self.settings[self.smtp_key]['smtp_port'],
                                               fromaddr=self.settings[self.smtp_key]['smtp_user'],
                                               toaddrs=self.settings[self.admin_emails],
                                               subject='Error {} {}:{}'.format(self.settings[self.host_name_key],
                                                                               self.settings[
                                                                                   self.service_name_key].upper(),
                                                                               self.settings[self.service_version_key]),
                                               capacity=1,
                                               password=self.settings[self.smtp_key]['smtp_password'])
                handler.setLevel(logging.ERROR)
                if not self.settings[self.ronin_key]:
                    return handler

    def get_http_service(self):
        from trellio.services import HTTPService
        http_service = None
        if HTTPService.__subclasses__():
            service_sub_class = HTTPService.__subclasses__()[0]

            http_service = service_sub_class(self.settings[self.service_name_key],
                                             self.settings[self.service_version_key],
                                             self.settings[self.http_host_key],
                                             self.settings[self.http_port_key])
        return http_service

    def get_tcp_service(self):
        from trellio.services import TCPService
        tcp_service = None
        if TCPService.__subclasses__():
            service_sub_class = TCPService.__subclasses__()[0]
            tcp_service = service_sub_class(self.settings[self.service_name_key],
                                            self.settings[self.service_version_key],
                                            self.settings[self.tcp_host_key],
                                            self.settings[self.tcp_port_key])
        return tcp_service

    def get_publisher(self):
        from trellio.pubsub import Publisher
        publisher = None
        if Publisher.__subclasses__():
            publisher_sub_class = Publisher.__subclasses__()[0]
            publisher = publisher_sub_class(self.settings[self.service_name_key],
                                            self.settings[self.service_version_key],
                                            self.settings[self.redis_host_key],
                                            self.settings[self.redis_port_key])
        return publisher

    def get_http_views(self):
        from trellio.views import HTTPView
        return self.inheritors(HTTPView)

    def get_tcp_views(self):
        from trellio.views import TCPView
        return self.inheritors(TCPView)

    def import_class_from_path(self, path):
        broken = path.split('.')
        class_name = broken[-1]
        module_name = '.'.join(broken[:-1])
        module = importlib.import_module(module_name)
        class_value = getattr(module, class_name)
        return module, class_value

    def enable_middlewares(self, http_service=None, http_views=()):
        middlewares = self.settings[self.middleware_key] or []
        middle_cls = []
        for i in middlewares:
            module, class_value = self.import_class_from_path(i)
            if not class_value:
                raise InvalidConfigurationError
            else:
                middle_cls.append(class_value())

        if http_service:
            http_service.middlewares = middle_cls
        for view in http_views:
            view.middlewares = middle_cls

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

    @staticmethod
    def inheritors(klass):
        subclasses = set()
        work = [klass]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)
        return list(subclasses)
