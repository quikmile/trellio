from ..wrappers import Response


class Borg(object):
    __shared_state = dict()

    def __init__(self):
        self.__dict__ = self.__shared_state


class Singleton(object):
    _instance = None
    _init_ran = False

    def has_inited(self):
        return self._init_ran

    def init_done(self):
        self._init_ran = True

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance


def default_preflight_response(request):
    headers = {'Access-Control-Allow-Origin': '*',
               'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE',
               'Access-Control-Allow-Headers': 'Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Authorization, Access-Control-Request-Method, Access-Control-Request-Headers',
               'Access-Control-Allow-Credentials': 'true'}
    return Response(status=204, headers=headers)
