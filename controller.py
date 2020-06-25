import curses
import logging
from pathlib import Path

import terminal
from input_keys import InputKeys
from pane_manager import PaneManager


class Controller():
    def __init__(self, standard_screen):
        self.standard_screen = standard_screen
        curses.curs_set(False)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.cwd = str(Path.cwd())
        self.left_selected_line_i = 0
        self.main_selected_line_i = 0

        self.input_keys = InputKeys()
        self.pane_manager = PaneManager(standard_screen)

    def update(self):
        is_working = True
        while is_working:
            self.standard_screen.clear()
            left_lines = terminal.get_ls("..")
            main_lines = terminal.get_ls(self.cwd)
            child_path = main_lines[self.main_selected_line_i]
            right_lines = terminal.get_ls(child_path)

            self.pane_manager.render_panes(
                left_lines,
                main_lines,
                right_lines,
                self.left_selected_line_i,
                self.main_selected_line_i)

            self.standard_screen.refresh()
            self.pane_manager.refresh_panes()

            input_key = self.standard_screen.getkey()
            logging.info("input: {}".format(input_key))
            if input_key == self.input_keys.down_key:
                self.down(len(main_lines))
            elif input_key == self.input_keys.up_key:
                self.up(len(main_lines))
            # terminal.open()

    def down(self, main_lines_length):
        self.main_selected_line_i = (self.main_selected_line_i + 1) % main_lines_length

    def up(self, main_lines_length):
        self.main_selected_line_i = (self.main_selected_line_i - 1) % main_lines_length
