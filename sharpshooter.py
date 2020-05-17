import curses
import logging
from pathlib import Path

from cursed_window import CursedWindow
import terminal
from input_keys import InputKeys



def main(standard_screen):
    curses.curs_set(False)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    cwd = str(Path.cwd())
    log_filename = "{}/last_run.log".format(cwd)
    logging.basicConfig(filename=log_filename,level=logging.DEBUG,filemode='w')

    logging.info("sharpshooter started")
    logging.info("curses version: {}".format(str(curses.version.decode())))

    in_keys = InputKeys()


    screen_height, screen_width = standard_screen.getmaxyx()
    logging.debug("screen size WxH: {}x{}".format(screen_width, screen_height))
    window_width = screen_width // 3
    window_y = 1
    window_height = screen_height - window_y

    left_window = CursedWindow(1, window_y, window_width -1, window_height)
    main_window = CursedWindow(window_width, window_y, window_width, window_height)
    right_window = CursedWindow(window_width*2, window_y, window_width, window_height)

    is_working = True
    while is_working:
        standard_screen.clear()

        left_window.set_text_content(terminal.get_ls(".."))
        left_window.render()

        cwd_lines = terminal.get_ls(cwd)
        main_window.set_text_content(cwd_lines)
        main_window.render()

        child_path = cwd_lines[main_window.get_selected_line_i()]
        right_window.set_text_content(terminal.get_ls(child_path))
        right_window.render()

        standard_screen.refresh()
        left_window.refresh()
        main_window.refresh()
        right_window.refresh()

        input_key = standard_screen.getkey()
        logging.info("input: {}".format(input_key))
        if input_key == in_keys.down_key:
            main_window.increment_selected_line_i()
        #terminal.open()

curses.wrapper(main)
