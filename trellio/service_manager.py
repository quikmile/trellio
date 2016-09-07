import asyncio
from concurrent.futures import ProcessPoolExecutor

class TcpManager:
    pass

class PuBSubManager:
    PUBSUB_DELAY = 5

    def __init__(self, pubsub_host, pubsub_port, registry_client, ssl_context=None):
        self._host = pubsub_host
        self._port = pubsub_port
        self._pubsub_handler = None
        self._registry_client = registry_client
        self._clients = None
        self._pending_publishes = {}
        self._ssl_context = ssl_context

    async def create_pubsub_handler(self):
        self._pubsub_handler = PubSub(self._host, self._port)
        await self._pubsub_handler.connect()

    async def register_for_subscription(self, host, port, node_id, clients):
        self._clients = clients
        subscription_list = []
        xsubscription_list = []
        for client in clients:
            if isinstance(client, TCPServiceClient):
                for each in dir(client):
                    fn = getattr(client, each)
                    if callable(fn) and getattr(fn, 'is_subscribe', False):
                        subscription_list.append(self._get_pubsub_key(client.name, client.version, fn.__name__))
                    elif callable(fn) and getattr(fn, 'is_xsubscribe', False):
                        xsubscription_list.append((client.name, client.version, fn.__name__, getattr(fn, 'strategy')))
        self._registry_client.x_subscribe(host, port, node_id, xsubscription_list)
        await self._pubsub_handler.subscribe(subscription_list, handler=self.subscription_handler)

    def publish(self, service, version, endpoint, payload):
        endpoint_key = self._get_pubsub_key(service, version, endpoint)
        executor = ProcessPoolExecutor(2)  # min 2 should be set
        loop = asyncio.get_event_loop()
        fut1 = asyncio.ensure_future(
            loop.run_in_executor(executor,self._pubsub_handler.publish(endpoint_key, json.dumps(payload, cls=TrellioEncoder))))  # using process pool instead of asyncio.async
        fut2 = asyncio.ensure_future(
            loop.run_in_executor(executor,self.xpublish(service, version, endpoint, payload)))  # using process pool instead of asyncio.async


    def xpublish(self, service, version, endpoint, payload):
        subscribers = yield from self._registry_client.get_subscribers(service, version, endpoint)
        strategies = defaultdict(list)
        for subscriber in subscribers:
            strategies[(subscriber['name'], subscriber['version'])].append(
                (subscriber['host'], subscriber['port'], subscriber['node_id'], subscriber['strategy']))
        for key, value in strategies.items():
            publish_id = str(uuid.uuid4())
            future = asyncio.async(
                self._connect_and_publish(publish_id, service, version, endpoint, value, payload))
            self._pending_publishes[publish_id] = future

    def receive(self, packet, transport, protocol):#no need to change
        if packet['type'] == 'ack':
            future = self._pending_publishes.pop(packet['request_id'], None)
            if future:
                future.cancel()
                transport.close()

    def subscription_handler(self, endpoint, payload):
        service, version, endpoint = endpoint.split('/')
        client = [sc for sc in self._clients if (sc.name == service and sc.version == version)][0]
        func = getattr(client, endpoint)
        executor = ProcessPoolExecutor(2)#min 2 should be set
        loop = asyncio.get_event_loop()
        fut = asyncio.ensure_future(loop.run_in_executor(executor, func(*json.loads(payload))))#using process pool instead of asyncio.async
        # asyncio.async(func(**json.loads(payload)))
        return fut

    @staticmethod
    def _get_pubsub_key(service, version, endpoint):#no need to change
        return '/'.join((service, str(version), endpoint))

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



