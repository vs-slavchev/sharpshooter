"""Reads and writes to a config file."""
import os
import configparser

_DEFAULT_CONFIG = """[keys]
up = e
down = n
open_parent = k
open_child = i
quit = q
open_terminal = t
open_file = \\n
toggle_hidden = h
delete = x
new_folder = f
rename = r
copy = c
paste = p
cut = d
zip_unzip = z
mark_item = m
undo = u
toggle_hotkeys = ?

[settings]
show_hidden = False
show_hotkeys = True"""


class ConfigManager:
    def __init__(self):
        self.file_path = os.path.expanduser('~') + '/.sharpshooter_config'
        if not os.path.isfile(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write(_DEFAULT_CONFIG)
        self.config = configparser.ConfigParser()
        self.config.read_string(_DEFAULT_CONFIG)  # seeds defaults for any missing keys
        self.config.read(self.file_path)          # user values override

    def set_config_settings_value(self, key, value):
        self.config.set('settings', key, str(value))
        with open(self.file_path, 'w') as f:
            self.config.write(f)

    def get_key_for(self, command):
        return self.config['keys'][command].replace('\\n', '\n')

    def get_show_hidden(self):
        return self.config['settings'].getboolean('show_hidden')

    def get_show_hotkeys(self):
        return self.config['settings'].getboolean('show_hotkeys')
