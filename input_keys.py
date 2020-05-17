import curses
import logging
import configparser
from pathlib import Path

class InputKeys:
    def __init__(self):
        cwd = Path.cwd()
        config = configparser.ConfigParser()
        config.read("{}/config.txt".format(cwd))
            
        self.down_key = config['keys']['down']
        self.up_key = config['keys']['up']

    def receive_input(key):
        switch = {
                down_key: down,
                up_key: up
                }

    def down():
        # go down
        pass

    def up():
        # go up
        pass
