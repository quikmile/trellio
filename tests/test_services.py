# class TestService(TCPService):
#     def __init__(self, port):
#         super().__init__('TestService', 1, host_port=port)
#
#
# class ServiceTests(TestCase):
#     def setUp(self):
#         self._test_service = TestService(4500)
#
#     def test_service_identifier(self):
#         self.assertEquals(self._test_service.name, 'TestService'.lower())
#         self.assertEquals(self._test_service.version, str(1))

from japronto import Application


def hello(request):
    return request.Response(text='Hello world!')


app = Application()
app.router.add_route('/', hello)
app.run(debug=True,port=8000)
