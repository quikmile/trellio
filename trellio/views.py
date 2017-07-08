from .utils.helpers import Borg

__all__ = ['BaseHTTPView', 'BaseTCPView']


class BaseView(Borg):
    def __init__(self, table: str = ''):
        super(BaseView, self).__init__()
        self._table = table
        self._model = None


class BaseHTTPView(BaseView):
    '''base class for HTTP views'''

    def __init__(self, table: str = '', json_fields: list = ()):
        super(BaseHTTPView, self).__init__(table=table)


class BaseTCPView(BaseView):
    '''base class for TCP views'''

    def __init__(self, table: str = '', json_fields: list = ()):
        super(BaseTCPView, self).__init__(table=table)
