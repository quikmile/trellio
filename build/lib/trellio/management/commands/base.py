class ManagementCommand:
    name = ''

    def run(self):
        raise NotImplementedError


class ManagementRegistry:
    _management_reg = {}

    @classmethod
    def register(cls, command_cls):
        if issubclass(command_cls, ManagementCommand):
            cls._management_reg[command_cls.name] = command_cls

    @classmethod
    def get(cls, name):
        return cls._management_reg.get(name)
