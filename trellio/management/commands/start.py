import os
from trellio.conf_manager.conf_client import ConfigHandler
from trellio.management.exceptions import InvalidCMDArguments
from trellio.management.commands.base import ManagementCommand, ManagementRegistry

class TrellioHostCommand(ManagementCommand):

    '''
    usage:python manage.py start_service <config_path> <(optional)service_file_path>
    '''

    name = 'start_service'

    def __init__(self, args):
        from trellio.host import Host
        self.args = args
        self.host_class = Host
        self.config_manager = ConfigHandler(self.host_class)
        self.setup_config()

    def setup_config(self):
        try:
            self.config_manager.set_config(config_path=self.args[0])
        except IndexError:
            raise InvalidCMDArguments

    def setup(self):
        self.setup_environment_variables()
        self.config_manager.setup_host()

    def setup_environment_variables(self):
        try:
            os.environ['CONFIG_FILE'] = self.args[0]#config file path
        except IndexError:
            raise InvalidCMDArguments
        os.environ['DATABASE_SETTINGS'] = self.config_manager.get_database_settings()

    def run(self):
        self.setup()
        self.host_class.run()

ManagementRegistry.register(TrellioHostCommand)



