"""
    Reads and writes to a config file.
"""

import configparser
from pathlib import Path


class ConfigManager:
    def __init__(self):
        cwd = Path.cwd()
        self.file_path = "{}/config.txt".format(cwd)
        self.config = configparser.ConfigParser()
        self.config.read(self.file_path)

    def set_config_settings_value(self, key, value):
        self.config.set('settings', key, value)
        self.save_config()

    def save_config(self):
        with open(self.file_path, 'w') as configfile:
            self.config.write(configfile)

    def get_key_for(self, command):
        # in order to read strings with chars that need escaping we need to encode and then decode
        return str(self.config['keys'][command]).encode('latin1').decode('unicode_escape')

    def get_show_hidden(self):
        return self.config['settings'].getboolean('show_hidden')
