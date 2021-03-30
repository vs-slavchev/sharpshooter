import curses
import logging
from pathlib import Path

import terminal
from input_keys import InputKeys
from pane_manager import PaneManager


class Controller:
    def __init__(self, standard_screen):
        self.standard_screen = standard_screen
        curses.curs_set(False)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.cwd = str(Path.cwd()) + "/"
        self.left_selected_line_i = 0
        self.main_selected_line_i = 0

        self.input_keys = InputKeys()
        self.pane_manager = PaneManager(standard_screen)

    def update(self):
        is_working = True
        while is_working:
            self.standard_screen.clear()
            left_lines = terminal.get_ls(self.get_parent_directory(self.cwd))
            main_lines = terminal.get_ls(self.cwd)
            child_path = self.cwd + main_lines[self.main_selected_line_i]
            right_lines = terminal.get_ls(child_path)

            parent_folder = self.get_path_elements(self.cwd)[-1] + "/"
            logging.info("parent folder: {}".format(parent_folder))
            logging.info("left lines: {}".format(left_lines))
            self.left_selected_line_i = left_lines.index(parent_folder)

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
            elif input_key == self.input_keys.left_key:
                if len(self.cwd.split("/")) > 3: # first elem is empty because string starts with '/'
                    self.set_cwd_to_parent_directory()
            elif input_key == self.input_keys.right_key:
                self.open_folder(child_path)
            # terminal.open()

    def set_cwd_to_parent_directory(self):
        self.cwd = self.get_parent_directory(self.cwd)
        logging.debug("new upper cwd: {}".format(self.cwd))
        self.main_selected_line_i = self.left_selected_line_i

    def down(self, main_lines_length):
        self.main_selected_line_i = (self.main_selected_line_i + 1) % main_lines_length

    def up(self, main_lines_length):
        self.main_selected_line_i = (self.main_selected_line_i - 1) % main_lines_length

    def open_folder(self, child_path):
        self.main_selected_line_i = 0
        self.cwd = child_path

    def get_parent_directory(self, path):
        only_path_elements = self.get_path_elements(path)
        higher_path_elements = only_path_elements[:-1]  # drop last path element
        return "/" + "/".join(higher_path_elements) + "/"

    def get_path_elements(self, path):
        higher_folders = path.split("/")
        only_path_elements = list(filter(lambda path_elem: len(path_elem) > 0, higher_folders))
        return only_path_elements
