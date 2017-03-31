import os

from ...conf_manager.conf_client import ConfigHandler
from ...management.commands.base import ManagementCommand, ManagementRegistry
from ...management.exceptions import InvalidCMDArguments


class TrellioHostCommand(ManagementCommand):
    '''
    usage:python trellio.py start_service <config_path> <(optional)service_file_path>
    '''

    name = 'runserver'

    def parse_args(self, args):
        new_args = {}
        for ind, arg in enumerate(args):
            if '=' in arg:
                broken = arg.split('=')
                new_args[broken[0]] = broken[1]
            elif not new_args.get('config') and ind == 0:
                new_args['config'] = arg
        if not new_args.get('config'):
            new_args['config'] = os.path.abspath('./config.json')
        return new_args

    def __init__(self, args):
        from trellio.host import Host
        self.args = self.parse_args(args)
        self.host_class = Host
        self.config_manager = ConfigHandler(self.host_class)
        self.setup_config()

    def setup_config(self):
        try:
            self.config_manager.set_config(config_path=self.args['config'])
        except KeyError:
            raise InvalidCMDArguments('Please give config.json path!')

    def setup(self):
        self.setup_config()
        self.setup_environment_variables()
        self.config_manager.setup_host()

    def setup_environment_variables(self):
        pass  # todo not needed right now

    def run(self):
        self.setup()
        self.host_class._smpt_handler = self.config_manager.get_smtp_logging_handler()
        self.host_class.run()


ManagementRegistry.register(TrellioHostCommand)
