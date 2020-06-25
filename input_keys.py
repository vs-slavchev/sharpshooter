import configparser
from pathlib import Path


class InputKeys:
    def __init__(self):
        cwd = Path.cwd()
        config = configparser.ConfigParser()
        config.read("{}/config.txt".format(cwd))

        self.up_key = config['keys']['up']
        self.down_key = config['keys']['down']
