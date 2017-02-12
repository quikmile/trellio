class Borg(object):
    __shared_state = dict()

    def __init__(self):
        self.__dict__ = self.__shared_state


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance
