class ManagementCommandNotFound(Exception):
    pass


def execute_from_command_line(args):  # sys args
    command_name = args[1]
    command_args = args[2:]
    from trellio.management.commands.base import ManagementRegistry
    if not ManagementRegistry.get(command_name):
        raise ManagementCommandNotFound
    command_class = ManagementRegistry.get(command_name)
    command_class(command_args).run()
