import logging

from pathlib import Path
from terminal import Terminal


class Content:
    def __init__(self):
        self.parent_lines = []
        self.main_lines = []
        self.child_path = ""
        self.child_lines = []

        self.cwd = str(Path.cwd()) + "/"
        self.parent_pane_selected_line_i = 0
        self.main_pane_selected_line_i = 0

        self.terminal = Terminal()

    def recalculate_content(self):
        self.parent_lines = self.terminal.get_ls(self.parent_directory())
        self.main_lines = self.terminal.get_ls(self.cwd)
        self.child_path = ""
        self.child_lines = []
        if len(self.main_lines) > 0:
            self.child_path = self.cwd + self.currently_selected_item()
            self.child_lines = self.terminal.get_ls(self.child_path)
        if self.cwd == "/":
            self.parent_lines = []
        else:
            parent_folder = self.to_path_elements()[-1] + "/"
            logging.info("parent folder: {}".format(parent_folder))
            self.parent_pane_selected_line_i = self.parent_lines.index(parent_folder)

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

    def down(self):
        self.main_pane_selected_line_i = (self.main_pane_selected_line_i + 1) % len(self.main_lines)

    def up(self):
        self.main_pane_selected_line_i = (self.main_pane_selected_line_i - 1) % len(self.main_lines)

    def open_child(self):
        logging.debug("trying to open child: {}".format(self.child_path))
        child_exists = self.child_path != ""
        selected_is_folder = child_exists and self.currently_selected_item().endswith("/")
        if selected_is_folder:
            self.main_pane_selected_line_i = 0
            self.cwd = self.child_path

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

    def get_child_path(self):
        return self.child_path

    def get_renderable_content(self):
        return self.parent_lines,\
               self.main_lines,\
               self.child_lines,\
               self.parent_pane_selected_line_i,\
               self.main_pane_selected_line_i

    def get_cwd(self):
        return self.cwd

    def toggle_show_hidden(self):
        self.terminal.toggle_show_hidden()