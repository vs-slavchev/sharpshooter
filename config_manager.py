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

    def get_config(self):
        return self.config

    def save_config(self):
        with open(self.file_path, 'w') as configfile:
            self.config.write(configfile)
