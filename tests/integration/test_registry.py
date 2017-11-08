import multiprocessing

import requests
from aiohttp.web_response import json_response

from trellio import *
from trellio.registry import Repository, Registry

processes = []


class ServiceA(TCPService):
    def __init__(self):
        super().__init__("service_a", "1", host_port=8001, host_ip='0.0.0.0')

    @api
    async def echo(self, data):
        return data


class ServiceClientA(TCPServiceClient):
    def __init__(self):
        super(ServiceClientA, self).__init__("service_a", "1")

    @request
    def echo(self, data):
        return locals()


class ServiceB(HTTPService):
    def __init__(self):
        super().__init__("service_b", "1", host_port=8000, host_ip='0.0.0.0')
        self._client_a = ServiceClientA()

    @get(path="/{data}/")
    async def get_echo(self, request):
        data = request.match_info.get('data')
        d = await self._client_a.echo(data)
        return json_response(text=d)


class ServiceBTCP(TCPService):
    def __init__(self):
        super().__init__("service_b", "1", host_port=8003, host_ip='0.0.0.0')
        self._client_a = ServiceClientA()

    @api
    async def get_echo(self, data):
        data = request.match_info.get('data')
        d = await self._client_a.echo(data)
        return d


def start_registry():
    repository = Repository()
    registry = Registry('0.0.0.0', 4500, repository)
    registry.start()


def start_service_a():
    Host.configure(http_port=8002, tcp_port=8001, tcp_host='0.0.0.0', service_name="service_a", service_version="1")
    Host.attach_tcp_service(ServiceA())
    Host.run()


def start_service_b():
    client_a = ServiceClientA()
    service_b = ServiceB()
    tcp_service = ServiceBTCP()

    Host.configure(http_port=8000, tcp_port=8003, http_host='0.0.0.0', service_name="service_b", service_version="1",
                   registry_host='0.0.0.0', registry_port=4500)

    service_b.clients = [client_a]
    tcp_service.clients = [client_a]
    Host.attach_http_service(service_b)
    Host.attach_tcp_service(tcp_service)
    Host.run()


def setup_module():
    global processes
    for target in [start_registry, start_service_a, start_service_b]:
        p = multiprocessing.Process(target=target)
        p.start()
        processes.append(p)

        # allow the subsystems to start up.
        # sleep for awhile
        import time
        time.sleep(1)


def restart_service_a():
    processes[1].terminate()
    p = multiprocessing.Process(target=start_service_a)
    p.start()
    processes[1] = p
    import time
    time.sleep(1)


def teardown_module():
    for p in processes:
        p.terminate()


def test_service_b():
    url = 'http://0.0.0.0:8000/blah/'
    r = requests.get(url)
    assert r.text == 'blah'
    assert r.status_code == 200


if __name__ == "__main__":
    setup_module()
    restart_service_a()
    test_service_b()
