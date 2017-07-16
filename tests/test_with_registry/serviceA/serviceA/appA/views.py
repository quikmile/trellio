from trellio.views import HTTPView,TCPView
from trellio.services import api,get
from ..clients import ServiceBCLient


class TCPView1(TCPView):

    @api
    async def servicea_tcp_api1(self,params):
        return {'msg':'Success'}


class HTTPView1(HTTPView):

    @get(path='/serviceA/1/')
    async def enpoint_one(self,request):
        return await ServiceBCLient().serviceb_tcp_api1(params={})


