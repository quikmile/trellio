from trellio.views import TCPView
from trellio.services import api


class TCPView1(TCPView):

    @api
    async def serviceb_tcp_api1(self,params):
        return {'msg':'Success'}

