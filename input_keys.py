"""
    Reads the input keys from a config.
"""

import configparser
from pathlib import Path

from config_manager import ConfigManager


class InputKeys:
    def __init__(self):
        config_manager = ConfigManager()

        self.up_key = config_manager.get_key_for('up')
        self.down_key = config_manager.get_key_for('down')
        self.open_parent_key = config_manager.get_key_for('open_parent')
        self.open_child_key = config_manager.get_key_for('open_child')
        self.quit_key = config_manager.get_key_for('quit')
        self.open_terminal_key = config_manager.get_key_for('open_terminal')
        self.open_file = config_manager.get_key_for('open_file')
        self.toggle_show_hidden = config_manager.get_key_for('toggle_show_hidden')
        self.delete = config_manager.get_key_for('delete')
        self.make_new_folder = config_manager.get_key_for('make_new_folder')
        self.rename = config_manager.get_key_for('rename')
        self.copy = config_manager.get_key_for('copy')
        self.paste = config_manager.get_key_for('paste')
        self.cut = config_manager.get_key_for('cut')
        self.zip_unzip = config_manager.get_key_for('zip_unzip')
        self.toggle_mark_item = config_manager.get_key_for('toggle_mark_item')

