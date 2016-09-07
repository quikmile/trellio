class TcpManager:
    pass

class PuBSubManager:
    def publish(self, name, version, endpoint, payload):
        pass

    def xpublish(self, name, version, endpoint, payload, strategy):
        pass

class HttpManager:
    def send_http_request(self, app_name, name, version, method, entity,
                                                               params):
        pass

class MicroServiceManager:
    #who'll set transport
    def __init__(self, connection_types=()):#connectoin types - tcp,pub-sub,http and http is enabled by default
        connection_types = (i.strip().lower() for i in connection_types)
        if 'tcp' in connection_types:
            self.tcp_manager = TcpManager()
        if 'pubsub' in connection_types:
            self.pub_sub_manager = PuBSubManager()
        self.transport = None


    def initiate(self):
        pass



