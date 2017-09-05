import os

from aiohttp.web_response import Response

from trellio import TCPService, api, HTTPService, get, Host


class TestTCPService(TCPService):
    def __init__(self):
        super(TestTCPService, self).__init__('test_service', '1', host_ip='127.0.0.1', host_port=8001)

    @api
    async def echo(self, q):
        print(q, os.getpid())
        return q


class TestHTTPService(HTTPService):
    def __init__(self):
        super(TestHTTPService, self).__init__('test_service', '1', host_ip='127.0.0.1', host_port=8000)

    @get(path='/')
    async def echo(self, request):
        return Response(body="running test service ...")


if __name__ == "__main__":
    tcp_service = TestTCPService()
    http_service = TestHTTPService()
    Host.configure(workers=4, host_name='test_service')
    Host.attach_tcp_service(tcp_service)
    Host.attach_http_service(http_service)
    Host.run()
