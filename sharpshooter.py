"""
    Starting point of the program, contains the input controller and the update loop.
"""

import curses
import logging
import sys
import os

import controller


def incurses(standard_screen):
    set_up_logging()

    app_controller = controller.Controller(standard_screen)
    try:
        app_controller.run()
    except Exception as e:
        logging.exception(e)
        raise


def set_up_logging():
    log_filename = "{}/.sharpshooter.log".format(os.getenv("HOME"))
    logging.basicConfig(format='%(asctime)s:%(levelname)s %(message)s',
                        filename=log_filename, level=logging.INFO, filemode='w')
    logging.info("sharpshooter started")
    logging.info("Python version: {}".format(sys.version))
    logging.info("curses version: {}".format(str(curses.version.decode())))


def main():
    curses.wrapper(incurses)


if __name__ == '__main__':
    main()
