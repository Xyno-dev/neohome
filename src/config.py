import tomllib

class Config():
    def __init__(self, app):
        self.app = app

        self.reqs_device: list = ['enabled', 'name']
        try:
            with open('neohome.toml', 'rb') as f:
                self.config: dict = tomllib.load(f)
        except FileNotFoundError:
            self.app.notify("Error: neohome.toml not found", title="Config not found!", severity="error")

        if self.check_config() == False:
            self.app.notify("Error: missing values in neohome.toml", title="Missing values!", severity="error")

    def check_config(self):
        try:
            config = self.config.copy()
            if config['ip'] != None:
                config.pop('ip')

            if config['port'] != None:
                config.pop('port')

            checks: list[bool] = [
                True 
                for domain in config
                for device in config[domain]
                for req in self.reqs_device
                if config[domain][device][req] != None
            ]

            if len(checks) == len(config):
                return True

        except:
            return False

