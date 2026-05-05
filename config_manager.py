"""Reads and writes to a config file."""
import logging
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


class ConfigError(Exception):
    pass


class ConfigManager:
    def __init__(self):
        self.file_path = os.path.expanduser('~') + '/.sharpshooter_config'
        if not os.path.isfile(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write(_DEFAULT_CONFIG)
        self.config = configparser.ConfigParser()
        self.config.read_string(_DEFAULT_CONFIG)
        try:
            self.config.read(self.file_path)
        except configparser.Error as e:
            raise ConfigError(
                f"Config file is corrupt: {self.file_path}\n"
                f"  {e}\n"
                f"Fix: edit the file to correct the syntax, or delete it to reset to defaults."
            )
        self._validate_keys()
        self._validate_settings()

    def _validate_keys(self):
        seen = {}
        duplicates = []
        for command, raw_value in self.config['keys'].items():
            value = raw_value.replace('\\n', '\n')
            if value in seen:
                duplicates.append(f"  '{value}' is bound to both '{seen[value]}' and '{command}'")
            else:
                seen[value] = command
        if duplicates:
            raise ConfigError(
                f"Duplicate key bindings in {self.file_path}:\n"
                + "\n".join(duplicates)
                + f"\nFix: edit {self.file_path} so each key is assigned to only one command."
            )

    def _validate_settings(self):
        for setting in ('show_hidden', 'show_hotkeys'):
            try:
                self.config['settings'].getboolean(setting)
            except ValueError:
                raw = self.config['settings'].get(setting)
                raise ConfigError(
                    f"Invalid value for '{setting}' in {self.file_path}: '{raw}'\n"
                    f"Expected: True or False\n"
                    f"Fix: edit {self.file_path} and set '{setting} = True' or '{setting} = False'."
                )

    def set_config_settings_value(self, key, value):
        self.config.set('settings', key, str(value))
        try:
            with open(self.file_path, 'w') as f:
                self.config.write(f)
        except OSError as e:
            logging.error("Failed to save config to %s: %s", self.file_path, e)

    def get_key_for(self, command):
        return self.config['keys'][command].replace('\\n', '\n')

    def get_show_hidden(self):
        return self.config['settings'].getboolean('show_hidden')

    def get_show_hotkeys(self):
        return self.config['settings'].getboolean('show_hotkeys')
