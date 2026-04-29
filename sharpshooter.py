"""
    Starting point of the program, contains the input controller and the update loop.
"""

import curses
import logging
import sys
import os

import controller
from config_manager import ConfigManager, ConfigError


def incurses(standard_screen, config_manager):
    set_up_logging()

    app_controller = controller.Controller(standard_screen, config_manager)
    try:
        app_controller.run()
    except Exception as e:
        logging.exception(e)
        raise


def set_up_logging():
    state_dir = os.path.join(os.path.expanduser('~'), '.local', 'state', 'sharpshooter')
    os.makedirs(state_dir, exist_ok=True)
    log_filename = os.path.join(state_dir, 'sharpshooter.log')
    logging.basicConfig(format='%(asctime)s:%(levelname)s %(message)s',
                        filename=log_filename, level=logging.INFO, filemode='w')
    logging.info("sharpshooter started")
    logging.info("Python version: {}".format(sys.version))
    logging.info("curses version: {}".format(str(curses.version.decode())))


def main():
    try:
        config_manager = ConfigManager()
    except ConfigError as e:
        print(f"sharpshooter: {e}", file=sys.stderr)
        sys.exit(1)
    curses.wrapper(lambda screen: incurses(screen, config_manager))


if __name__ == '__main__':
    main()
