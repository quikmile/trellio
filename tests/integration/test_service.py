from trellio import TCPService, api, Host


class TestService(TCPService):
    def __init__(self):
        super(TestService, self).__init__('test_service', '1', host_ip='127.0.0.1', host_port=8001)

    @api
    async def echo(self):
        return "echo"


if __name__ == "__main__":
    test_service = TestService()
    Host.configure()

    Host.attach_tcp_service(test_service)
    Host.run()
