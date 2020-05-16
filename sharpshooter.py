import curses
import logging

import cursed_window
import terminal

logging.basicConfig(filename='last_run.log',level=logging.DEBUG,filemode='w')

def main(standard_screen):
    curses.curs_set(False)
    standard_screen.clear()
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    logging.debug("started")
    screen_height, screen_width = standard_screen.getmaxyx()
    logging.debug("screen size WxH: {}".format(screen_width, screen_height))
    window_width = screen_width // 3

    main_window = cursed_window.CursedWindow(2, 1, window_width, 20)
    main_window.set_text_content(terminal.get_ls())
    main_window.render()

    standard_screen.refresh()
    main_window.refresh()

    standard_screen.getkey()
    terminal.open()

curses.wrapper(main)
