import curses
import logging

import cursed_window
import terminal

logging.basicConfig(filename='last_run.log',level=logging.DEBUG,filemode='w')

def main(standard_screen):
    curses.curs_set(False)
    standard_screen.clear()
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    logging.info("sharpshooter started")
    logging.info("curses version: {}".format(str(curses.version.decode())))
    screen_height, screen_width = standard_screen.getmaxyx()
    logging.debug("screen size WxH: {}".format(screen_width, screen_height))
    window_width = screen_width // 3

    selected_line_i = 0

    left_window = cursed_window.CursedWindow(1, 1, window_width -1, screen_height)
    left_window.set_text_content(terminal.get_ls(".."))
    left_window.render()

    cwd_lines = terminal.get_ls()
    main_window = cursed_window.CursedWindow(window_width, 1, window_width, screen_height)
    main_window.set_text_content(cwd_lines)
    main_window.render()

    right_window = cursed_window.CursedWindow(window_width*2, 1, window_width, screen_height)
    right_window.set_text_content(terminal.get_ls(cwd_lines[selected_line_i]))
    right_window.render()

    standard_screen.refresh()
    left_window.refresh()
    main_window.refresh()
    right_window.refresh()

    standard_screen.getkey()
    #terminal.open()

curses.wrapper(main)
