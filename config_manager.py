"""
    Reads and writes to a config file.
"""

import os
import configparser
from pathlib import Path


default_config = """[keys]
                    up = e
                    down = n
                    open_parent = k
                    open_child = i
                    quit = q
                    open_terminal = t
                    open_file = \\n
                    toggle_show_hidden = h
                    delete = x
                    make_new_folder = f
                    rename = r
                    copy = c
                    paste = p
                    cut = d
                    zip_unzip = z
                    toggle_mark_item = m
                    undo = u
                    
                    [settings]
                    show_hidden = False"""


class ConfigManager:
    def __init__(self):
        home_dir = Path.home()
        self.file_path = "{}/.sharpshooter_config".format(home_dir)

        if not os.path.isfile(self.file_path):
            with open(self.file_path, 'w+') as new_file:
                new_file.write(default_config)

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
