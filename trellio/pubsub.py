import asyncio
import logging

import asyncio_redis as redis

from .utils.jsonencoder import TrellioEncoder

try:
    import ujson as json
except:
    import json


class PubSub:
    """
    Pub sub handler which uses redis.
    Can be used to publish an event or subscribe to a list of endpoints
    """

    def __init__(self, redis_host, redis_port):
        """
        Create in instance of Pub Sub handler
        :param str redis_host: Redis Host address
        :param redis_port: Redis port number
        """
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._conn = None
        self._logger = logging.getLogger(__name__)

    async def connect(self):
        """
        Connect to the redis server and return the connection
        :return:
        """
        self._conn = await self._get_conn()
        return self._conn

    async def publish(self, endpoint: str, payload: str):
        """
        Publish to an endpoint.
        :param str endpoint: Key by which the endpoint is recognised.
                         Subscribers will use this key to listen to events
        :param str payload: Payload to publish with the event
        :return: A boolean indicating if the publish was successful
        """
        if self._conn is not None:
            try:
                await self._conn.publish(endpoint, payload)
                return True
            except redis.Error as e:
                self._logger.error('Publish failed with error %s', repr(e))
        return False

    async def subscribe(self, endpoints: list, handler):
        """
        Subscribe to a list of endpoints
        :param endpoints: List of endpoints the subscribers is interested to subscribe to
        :type endpoints: list
        :param handler: The callback to call when a particular event is published.
                        Must take two arguments, a channel to which the event was published
                        and the payload.
        :return:
        """
        connection = await self._get_conn()
        subscriber = await connection.start_subscribe()
        await subscriber.subscribe(endpoints)
        while True:
            payload = await subscriber.next_published()
            handler(payload.channel, payload.value)

    async def _get_conn(self):
        return await redis.Connection.create(self._redis_host, self._redis_port, auto_reconnect=True)


class Publisher:
    def __init__(self, service_name, service_version, pubsub_host, pubsub_port):
        self._service_name = service_name
        self._service_version = service_version
        self._host = pubsub_host
        self._port = pubsub_port
        self._pubsub_handler = None

    @property
    def service_name(self):
        return self._service_name

    @property
    def service_version(self):
        return self._service_version

    @property
    def pubsub_bus(self):
        return self._pubsub_bus

    @pubsub_bus.setter
    def pubsub_bus(self, bus):
        self._pubsub_bus = bus

    def create_pubsub_handler(self):
        self._pubsub_handler = PubSub(self._host, self._port)
        asyncio.async(self._pubsub_handler.connect())

    def _publish(self, endpoint, payload):
        channel = self._get_pubsub_channel(endpoint)
        asyncio.async(self._pubsub_handler.publish(channel, json.dumps(payload, cls=TrellioEncoder)))

    def _get_pubsub_channel(self, endpoint):
        return '/'.join((self.service_name, str(self.service_version), endpoint))


class Subscriber:
    def __init__(self, service_name, service_version, pubsub_host=None, pubsub_port=None):
        self._service_name = service_name
        self._service_version = service_version
        self._host = pubsub_host
        self._port = pubsub_port
        self._pubsub_handler = None

    @property
    def service_name(self):
        return self._service_name

    @property
    def service_version(self):
        return self._service_version

    def create_pubsub_handler(self):
        self._pubsub_handler = PubSub(self._host, self._port)
        asyncio.async(self._pubsub_handler.connect())

    def _get_pubsub_channel(self, endpoint):
        return '/'.join((self.service_name, str(self.service_version), endpoint))

    def register_for_subscription(self):
        subscription_list = []
        for each in dir(self.__class__):
            fn = getattr(self.__class__, each)
            if callable(fn) and getattr(fn, 'is_subscribe', False):
                subscription_list.append(self._get_pubsub_channel(fn.__name__))
        asyncio.async(self._pubsub_handler.subscribe(subscription_list, handler=self.subscription_handler))

    def subscription_handler(self, endpoint, payload):
        func = getattr(self.__class__, endpoint)
        asyncio.async(func(**json.loads(payload)))
