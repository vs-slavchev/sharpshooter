"""
    Reads the input keys from a config.
"""

import re

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
        self.toggle_hidden = config_manager.get_key_for('toggle_hidden')
        self.delete = config_manager.get_key_for('delete')
        self.new_folder = config_manager.get_key_for('new_folder')
        self.rename = config_manager.get_key_for('rename')
        self.copy = config_manager.get_key_for('copy')
        self.paste = config_manager.get_key_for('paste')
        self.cut = config_manager.get_key_for('cut')
        self.zip_unzip = config_manager.get_key_for('zip_unzip')
        self.mark_item = config_manager.get_key_for('mark_item')
        self.undo = config_manager.get_key_for('undo')

        self.hotkey_guide = self.generate_hotkey_guide()

    def generate_hotkey_guide(self):
        keys_to_display_in_guide = [
            self.format_hotkey_description(self.new_folder, 'new_folder'),
            self.format_hotkey_description(self.rename, 'rename'),
            self.format_hotkey_description(self.zip_unzip, 'zip_unzip'),
            self.format_hotkey_description(self.delete, 'delete'),
            self.format_hotkey_description(self.copy, 'copy'),
            self.format_hotkey_description(self.cut, 'cut'),
            self.format_hotkey_description(self.paste, 'paste'),
            self.format_hotkey_description(self.toggle_hidden, 'toggle_hidden'),
            self.format_hotkey_description(self.mark_item, 'mark_item'),
            self.format_hotkey_description(self.undo, 'undo'),
            self.format_hotkey_description(self.quit_key, 'quit')
        ]
        return "Keys: " + "; ".join(keys_to_display_in_guide)

    @staticmethod
    def format_hotkey_description(key, action_name):
        if key not in action_name:
            return '{} - {}'.format(action_name, key)
        else:
            action_name = action_name.replace('_', ' ')
            action_name_pattern = r'([a-z_]*)' + key + r'([a-z_]*)'
            result_pattern = r'\g<1>(' + key + r')\g<2>'
            return re.sub(action_name_pattern, result_pattern, action_name, count=1)
