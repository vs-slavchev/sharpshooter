"""
    Starting point of the program, contains the input controller and the update loop.
"""

import curses
import logging
import traceback
from pathlib import Path

from controller import Controller


def incurses(standard_screen):
    set_up_logging()

    controller = Controller(standard_screen)
    try:
        controller.update()
    except Exception:
        logging.error(traceback.format_exc())
        raise


def set_up_logging():
    log_filename = "{}/last_run.log".format(Path.cwd())
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, filemode='w')
    logging.info("sharpshooter started")
    logging.info("curses version: {}".format(str(curses.version.decode())))


def main():
    curses.wrapper(incurses)


if __name__ == '__main__':
    main()