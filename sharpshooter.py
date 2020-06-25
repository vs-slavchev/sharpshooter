import curses
import logging
from pathlib import Path

from controller import Controller


def main(standard_screen):
    set_up_logging()

    controller = Controller(standard_screen)
    controller.update()


def set_up_logging():
    log_filename = "{}/last_run.log".format(Path.cwd())
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, filemode='w')
    logging.info("sharpshooter started")
    logging.info("curses version: {}".format(str(curses.version.decode())))


curses.wrapper(main)
