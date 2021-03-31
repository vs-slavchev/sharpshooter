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

        self.parent_lines = []
        self.main_lines = []
        self.child_lines = []

        self.cwd = str(Path.cwd()) + "/"
        self.parent_pane_selected_line_i = 0
        self.main_pane_selected_line_i = 0

        self.input_keys = InputKeys()
        self.pane_manager = PaneManager(standard_screen)

    def update(self):
        is_working = True
        while is_working:
            self.standard_screen.clear()

            self.parent_lines = terminal.get_ls(self.parent_directory())
            self.main_lines = terminal.get_ls(self.cwd)
            child_path = ""
            self.child_lines = []
            if len(self.main_lines) > 0:
                child_path = self.cwd + self.currently_selected_item()
                self.child_lines = terminal.get_ls(child_path)

            if self.cwd == "/":
                self.parent_lines = []
            else:
                parent_folder = self.to_path_elements()[-1] + "/"
                logging.info("parent folder: {}".format(parent_folder))
                self.parent_pane_selected_line_i = self.parent_lines.index(parent_folder)

            self.pane_manager.render_panes(
                self.parent_lines,
                self.main_lines,
                self.child_lines,
                self.parent_pane_selected_line_i,
                self.main_pane_selected_line_i)

            self.standard_screen.refresh()
            self.pane_manager.refresh_panes()

            input_key = self.standard_screen.getkey()
            logging.info("input: {}".format(input_key))
            if input_key == self.input_keys.down_key:
                self.down(len(self.main_lines))
            elif input_key == self.input_keys.up_key:
                self.up(len(self.main_lines))
            elif input_key == self.input_keys.open_parent_key:
                self.open_parent()
            elif input_key == self.input_keys.open_child_key:
                self.open_child(child_path)
            elif input_key == self.input_keys.quit_key:
                is_working = False
            # terminal.open()

    def open_parent(self):
        there_is_some_parent = len(self.to_path_elements()) > 0
        if there_is_some_parent:
            self.set_cwd_to_parent_directory()

    def currently_selected_item(self):
        return self.main_lines[self.main_pane_selected_line_i]

    def set_cwd_to_parent_directory(self):
        self.cwd = self.parent_directory()
        logging.debug("new upper cwd: {}".format(self.cwd))
        self.main_pane_selected_line_i = self.parent_pane_selected_line_i

    def down(self, main_lines_length):
        self.main_pane_selected_line_i = (self.main_pane_selected_line_i + 1) % main_lines_length

    def up(self, main_lines_length):
        self.main_pane_selected_line_i = (self.main_pane_selected_line_i - 1) % main_lines_length

    def open_child(self, child_path):
        child_exists = child_path != ""
        selected_is_folder = child_exists and self.currently_selected_item().endswith("/")
        if selected_is_folder:
            self.main_pane_selected_line_i = 0
            self.cwd = child_path

    def parent_directory(self):
        higher_path_elements = self.get_higher_path_elements()
        if len(higher_path_elements) > 0:
            return "/" + "/".join(higher_path_elements) + "/"
        else:
            return "/"

    def get_higher_path_elements(self):
        only_path_elements = self.to_path_elements()
        higher_path_elements = only_path_elements[:-1]  # drop last path element
        return higher_path_elements

    def to_path_elements(self):
        higher_folders = self.cwd.split("/")
        only_path_elements = list(filter(lambda path_elem: len(path_elem) > 0, higher_folders))
        return only_path_elements
