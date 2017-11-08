from trellio import TCPService, api, Host


class ServiceTest(TCPService):
    def __init__(self):
        super().__init__('test_service', '1')

    @api
    async def echo(self):
        return "echo"


if __name__ == "__main__":
    test_service = ServiceTest()
    Host.configure(tcp_port=8001)

    Host.attach_tcp_service(test_service)
    Host.run()
