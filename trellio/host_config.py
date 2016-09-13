class HostManager:

    def __init__(self, f_loc, service_id, registry):
        self.f_loc = f_loc
        self.f_handler = yield from open(f_loc, 'rb')
        self.service_id = service_id
        self.reg = registry


    def validate(self):
        self.reg.inspect_service(self.service_id)
        self.validate_config_file()

    def validate_config_file(self):
        if not self.f_handler:
            raise Exception('invalid config file')

    def instantiate_host(self):
        pass#todo instantiate host instance like in __main__,
        #only manager


class HostManagerCollection:
    pass #tothink