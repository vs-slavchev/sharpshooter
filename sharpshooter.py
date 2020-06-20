import curses
import logging
from pathlib import Path

import terminal
from input_keys import InputKeys
from pane_manager import PaneManager


def main(standard_screen):
    curses.curs_set(False)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    set_up_logging()
    in_keys = InputKeys()
    pane_manager = PaneManager(standard_screen)

    cwd = str(Path.cwd())
    left_selected_line_i = 0
    main_selected_line_i = 0

    is_working = True
    while is_working:
        standard_screen.clear()
        left_lines = terminal.get_ls("..")
        main_lines = terminal.get_ls(cwd)
        child_path = main_lines[main_selected_line_i]
        right_lines = terminal.get_ls(child_path)

        pane_manager.render_panes(left_lines, main_lines, right_lines,
                                  left_selected_line_i, main_selected_line_i)

        standard_screen.refresh()
        pane_manager.refresh_panes()

        input_key = standard_screen.getkey()
        logging.info("input: {}".format(input_key))
        if input_key == in_keys.down_key:
            main_selected_line_i = (main_selected_line_i + 1) % len(main_lines)
        elif input_key == in_keys.up_key:
            main_selected_line_i = (main_selected_line_i - 1) % len(main_lines)
        #terminal.open()


def set_up_logging():
    log_filename = "{}/last_run.log".format(Path.cwd())
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, filemode='w')
    logging.info("sharpshooter started")
    logging.info("curses version: {}".format(str(curses.version.decode())))


curses.wrapper(main)
