class InvalidSignalType(Exception):
    pass

class BaseSignal:
    _registry_list = []

    @classmethod
    def register(cls, to_register, soft=False):
        cls._registry_list.append([to_register, soft])

    @classmethod
    async def _run(cls, *args, **kwargs):
        print('service ready run called')
        for i in cls._registry_list:
            try:
                await i[0](*args, **kwargs)
            except Exception as e:
                if not i[1]:
                    raise e


class ServiceReady(BaseSignal):
    _registry_list = []


def register(signal_type,soft=False):

    def decorator(receiver):
        if not issubclass(signal_type, BaseSignal):
            raise InvalidSignalType
        signal_type.register(receiver,soft)
        return receiver
    return decorator

