class BaseSignal:
    _registry_list = []

    @classmethod
    def register(cls, to_register, soft=False):
        cls._registry_list.append([to_register, soft])

    @classmethod
    async def _run(cls, *args, **kwargs):
        for i in cls._registry_list:
            try:
                await i[0](*args, **kwargs)
            except Exception as e:
                if not i[1]:
                    raise e


class ServiceReady(BaseSignal):
    _registry_list = []
