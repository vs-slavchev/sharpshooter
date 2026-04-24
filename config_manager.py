"""Reads and writes the TOML config file."""
import os

try:
    import tomllib
except ImportError:
    import tomli as tomllib
import tomli_w

_DEFAULTS = {
    'keys': {
        'up': 'e', 'down': 'n', 'open_parent': 'k', 'open_child': 'i',
        'quit': 'q', 'open_terminal': 't', 'open_file': '\n',
        'toggle_hidden': 'h', 'delete': 'x', 'new_folder': 'f',
        'rename': 'r', 'copy': 'c', 'paste': 'p', 'cut': 'd',
        'zip_unzip': 'z', 'mark_item': 'm', 'undo': 'u', 'toggle_hotkeys': '?',
    },
    'settings': {'show_hidden': False, 'show_hotkeys': True},
}


class ConfigManager:
    def __init__(self):
        self.file_path = os.path.expanduser('~') + '/.sharpshooter_config'
        self.config = self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            cfg = _copy(_DEFAULTS)
            self._write(cfg)
            return cfg
        with open(self.file_path, 'rb') as f:
            return _merge(_DEFAULTS, tomllib.load(f))

    def _write(self, cfg):
        with open(self.file_path, 'wb') as f:
            tomli_w.dump(cfg, f)

    def set_config_settings_value(self, key, value):
        self.config['settings'][key] = value
        self._write(self.config)

    def get_key_for(self, command):
        return self.config['keys'].get(command, _DEFAULTS['keys'].get(command, ''))

    def get_show_hidden(self):
        return self.config['settings'].get('show_hidden', False)

    def get_show_hotkeys(self):
        return self.config['settings'].get('show_hotkeys', True)


def _copy(d):
    return {k: dict(v) if isinstance(v, dict) else v for k, v in d.items()}


def _merge(base, override):
    out = _copy(base)
    for section, values in override.items():
        if section in out and isinstance(values, dict):
            out[section].update(values)
        else:
            out[section] = values
    return out
