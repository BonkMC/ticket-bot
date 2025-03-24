import configparser
import os


class AppConfig:
    def __init__(self, file_name="secrets.ini", cfg_dir=os.path.expanduser("~")):
        if cfg_dir is None:
            cfg_dir = os.path.expanduser("~")
        self.cfg_dir = os.path.join(cfg_dir, ".pyconfig")
        self.config_file = os.path.join(self.cfg_dir, file_name)
        if not os.path.isdir(self.cfg_dir):
            raise Exception("Directory {} does not exist".format(self.cfg_dir))

        if not os.path.isfile(self.config_file):
            raise Exception("Configuration file {} does not exist".format(self.config_file))

        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

    def get_bot_key(self):
        main_section = self.config['main']
        return main_section['bot_token']

    def get_config_dir(self):
        return self.cfg_dir


if __name__ == '__main__':
    app_config = AppConfig()
    print(app_config.get_bot_key())
