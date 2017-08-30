from trellio.services import TCPServiceClient,request


class ServiceBCLient(TCPServiceClient):

    def __init__(self):
        super(ServiceBCLient,self).__init__('serviceB','1')

    @request
    def serviceb_tcp_api1(self, params):
        return locals()

