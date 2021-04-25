import configparser
from pathlib import Path

from config_manager import ConfigManager


class InputKeys:
    def __init__(self):
        config_manager = ConfigManager()
        config = config_manager.get_config()

        self.up_key = config['keys']['up']
        self.down_key = config['keys']['down']
        self.open_parent_key = config['keys']['open_parent']
        self.open_child_key = config['keys']['open_child']
        self.quit_key = config['keys']['quit']
        self.open_terminal_key = config['keys']['open_terminal']
        # in order to read strings with chars that need escaping we need to encode and then decode
        self.open_file = str(config['keys']['open_file']).encode('latin1').decode('unicode_escape')
        self.toggle_show_hidden = config['keys']['toggle_show_hidden']
        self.delete = config['keys']['delete']
        self.make_new_folder = config['keys']['make_new_folder']
        self.rename = config['keys']['rename']
        self.copy = config['keys']['copy']
        self.paste = config['keys']['paste']
        self.cut = config['keys']['cut']
        self.zip_unzip = config['keys']['zip_unzip']

