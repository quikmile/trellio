from trellio.conf_manager.conf_client import ConfigHandler

class TrellioHostManager:

    def __init__(self, host_class):
        self.config_manager = ConfigHandler(host_class)

    def setup(self):
        http_service = self.config_manager.get_http_service()
        tcp_service = self.config_manager.get_tcp_service()


if __name__ == '__main__':
    import sys

