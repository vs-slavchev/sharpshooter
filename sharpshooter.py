import curses
import logging

logging.basicConfig(filename='last_run.log',level=logging.DEBUG,filemode='w')

def main(standard_screen):
    curses.curs_set(False)
    standard_screen.clear()

    logging.debug("started")

    standard_screen.addstr("mandatory curse word to test")

    standard_screen.refresh()
    standard_screen.getkey()

curses.wrapper(main)
