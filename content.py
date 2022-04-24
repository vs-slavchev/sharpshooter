"""
    Contains the state of the application - panes, current working directory, selected lines.
"""

import logging
import terminal
import shutil
import threading

from config_manager import ConfigManager
from fs_item import FsItem
import utility


class Content:
    def __init__(self):
        self.parent_lines = []
        self.main_lines = []
        self.child_path = ""
        self.child_lines = []

        self.cwd = terminal.provide_initial_cwd()
        self.parent_pane_selected_line_i = 0
        self.main_pane_selected_line_i = 0

        self.path_to_copy = ""
        self.copy_removes_source = False

        self.marked_item_indices = []

        self.config_manager = ConfigManager()
        self.show_hidden = self.config_manager.get_show_hidden()

        self.recalculate_content()

    def toggle_show_hidden(self):
        logging.info("action: toggling hide/show hidden files from: {}".format(self.show_hidden))
        self.show_hidden = not self.show_hidden

        if not utility.is_hidden(self.currently_selected_item().text):
            self.recalculate_same_selected_line()
        else:
            self.select_closest_to_hidden_item()

        # save change to the config file
        value_to_write = str(self.show_hidden)
        self.config_manager.set_config_settings_value('show_hidden', value_to_write)

    # the position of the selected line might change if items before it are hidden, but we want the same item
    # to be selected after hiding or showing
    def recalculate_same_selected_line(self):
        selected_item = self.currently_selected_item()
        self.main_lines = self.query_pane_content(self.cwd)
        self.main_pane_selected_line_i = self.main_lines.index(selected_item)

    # hiding a hidden item; only happens when hiding because only then can a hidden item be selected
    def select_closest_to_hidden_item(self):
        from_selected_to_start = list(range(self.main_pane_selected_line_i - 1, 0, -1))
        from_selected_to_end = list(range(self.main_pane_selected_line_i + 1, len(self.main_lines) - 1, 1))
        indices_to_iterate = from_selected_to_start + from_selected_to_end
        closest_visible_item = ""
        for item_i in indices_to_iterate:
            item = self.main_lines[item_i]
            if not utility.is_hidden(item):
                closest_visible_item = item
                break
        self.main_lines = self.query_pane_content(self.cwd)
        self.main_pane_selected_line_i = self.main_lines.index(closest_visible_item)

    # returns the lines that represent the files and folders in the path_to_folder
    def query_pane_content(self, path_to_folder):
        pane_content = terminal.get_ls(path_to_folder)

        if not self.show_hidden:
            pane_content = list(filter(lambda l: not utility.is_hidden(l.text), pane_content))

        return pane_content

    def query_parent_pane_content(self):
        pane_content = terminal.get_ls(self.parent_directory())

        if not self.show_hidden:
            selected_parent_item = self.get_parent_folder()
            pane_content = list(filter(
                lambda l: not utility.is_hidden(l.text) or l.text == selected_parent_item, pane_content))

        return pane_content

    def recalculate_content(self):
        self.parent_lines = self.query_parent_pane_content()
        self.main_lines = self.query_pane_content(self.cwd)
        self.child_path = ""
        self.child_lines = []
        if len(self.main_lines) > 0:
            self.child_path = self.cwd + self.currently_selected_item().text
            if utility.is_folder(self.child_path):
                self.child_lines = self.query_pane_content(self.child_path)
            else:
                self.child_lines = []
        if self.cwd == "/":
            self.parent_lines = []
        else:
            parent_folder = self.get_parent_folder()
            logging.info("parent folder: {}".format(parent_folder))
            self.parent_pane_selected_line_i = list(map(lambda pl: pl.text, self.parent_lines)) \
                .index(parent_folder)

    def get_parent_folder(self):
        path_elements = self.to_path_elements()
        if len(path_elements) > 0:
            return path_elements[-1] + "/"
        else:
            return ""

    def open_parent(self):
        logging.info("action: open_parent")
        there_is_some_parent = len(self.to_path_elements()) > 0
        if there_is_some_parent:
            self.set_cwd_to_parent_directory()
            self.unmark_any_marked_items()

    def currently_selected_item(self):
        if self.main_pane_selected_line_i >= len(self.main_lines):
            self.main_pane_selected_line_i = len(self.main_lines) - 1
        return self.main_lines[self.main_pane_selected_line_i]

    def set_cwd_to_parent_directory(self):
        self.cwd = self.parent_directory()
        logging.debug("new upper cwd: {}".format(self.cwd))
        self.main_pane_selected_line_i = self.parent_pane_selected_line_i

    def down(self):
        logging.info("action: down")
        if self.no_main_lines_exist():
            return
        self.main_pane_selected_line_i = (self.main_pane_selected_line_i + 1) % len(self.main_lines)

    def up(self):
        logging.info("action: up")
        if self.no_main_lines_exist():
            return
        self.main_pane_selected_line_i = (self.main_pane_selected_line_i - 1) % len(self.main_lines)

    def open_child(self):
        logging.debug("action: open_child: {}".format(self.child_path))
        child_exists = self.child_path != ""
        selected_is_folder = child_exists and self.currently_selected_item().is_folder()
        if selected_is_folder:
            self.main_pane_selected_line_i = 0
            self.cwd = self.child_path
            self.unmark_any_marked_items()

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
        for marked_index in self.marked_item_indices:
            self.main_lines[marked_index].is_marked = True

        return self.parent_lines, \
            self.main_lines, \
            self.child_lines, \
            self.parent_pane_selected_line_i, \
            self.main_pane_selected_line_i

    def get_cwd(self):
        return self.cwd

    def open_selected(self):
        if self.currently_selected_item().is_folder():
            self.open_child()
        else:
            terminal.open_file(self.get_child_path())

    def delete_selected(self):
        logging.info("action: delete selected")
        if self.no_main_lines_exist():
            return
        exist_marked_items = len(self.marked_item_indices) > 0
        if exist_marked_items:
            paths_to_delete = map(lambda mii: self.cwd + self.main_lines[mii].text, self.marked_item_indices)
            for path in paths_to_delete:
                terminal.delete(path)
            self.unmark_any_marked_items()
        else:
            terminal.delete(self.child_path)
            self.unmark_any_marked_items()
        self.main_pane_selected_line_i = min(self.main_pane_selected_line_i, len(self.main_lines) - 1)

    def make_new_folder(self, new_folder_name):
        logging.info("action: make new folder")
        terminal.make_new_folder(self.cwd + new_folder_name)
        self.unmark_any_marked_items()

    def rename(self, old_name, new_name):
        logging.info("action: rename")
        if self.no_main_lines_exist():
            return
        old_path = self.cwd + old_name
        new_path = self.cwd + new_name
        terminal.move(old_path, new_path)

    def get_num_main_lines(self):
        return len(self.main_lines)

    def get_main_selected_line_i(self):
        return self.main_pane_selected_line_i

    def no_main_lines_exist(self):
        return len(self.main_lines) <= 0

    def copy_selected(self):
        logging.info("action: copy")
        if self.no_main_lines_exist():
            return
        self.path_to_copy = self.get_child_path()
        self.copy_removes_source = False
        logging.info("copy clipboard: {}".format(self.path_to_copy))

    def paste(self):
        logging.info("action: paste")
        if self.path_to_copy == "":
            return
        folder_to_paste_in = self.cwd

        if self.copy_removes_source:
            terminal.move(self.path_to_copy, folder_to_paste_in)
        else:
            terminal.paste(self.path_to_copy, folder_to_paste_in)

        self.main_lines = self.query_pane_content(self.cwd)
        newly_pasted_item = FsItem(utility.extract_item_name_from_path(self.path_to_copy))
        self.main_pane_selected_line_i = self.main_lines.index(newly_pasted_item)

        self.path_to_copy = ""
        self.copy_removes_source = False

    def cut_selected(self):
        logging.info("action: cut")
        if self.no_main_lines_exist():
            return
        self.path_to_copy = self.get_child_path()
        self.copy_removes_source = True
        logging.info("cut clipboard: {}".format(self.path_to_copy))

    def zip_unzip(self):
        logging.info("action: zip unzip")
        if self.no_main_lines_exist():
            return

        format_abbreviation = ".zip"
        if self.currently_selected_item().text.endswith(format_abbreviation):
            self.unzip(format_abbreviation)
        else:
            self.zip()

    def zip(self):
        logging.info("action: zip")
        path_to_process = self.cwd + self.currently_selected_item().text
        zip_file_name = self.currently_selected_item().get_clean_name()
        thread = threading.Thread(target=shutil.make_archive,
                                  args=(self.cwd + zip_file_name, 'zip', path_to_process,))
        thread.start()

    def unzip(self, format_abbreviation):
        logging.info("action: unzip")
        currently_selected_text = self.currently_selected_item().text
        path_to_process = self.cwd + currently_selected_text
        folder_to_unpack_in = self.cwd + currently_selected_text[:-len(format_abbreviation)]
        thread = threading.Thread(target=shutil.unpack_archive,
                                  args=(path_to_process, folder_to_unpack_in, 'zip'))
        thread.start()

    def open_new_terminal(self):
        terminal.open_new_terminal(self.cwd)

    def toggle_mark_item(self):
        is_already_marked = self.main_pane_selected_line_i in self.marked_item_indices
        if is_already_marked:
            self.marked_item_indices.remove(self.main_pane_selected_line_i)
        else:
            self.marked_item_indices.append(self.main_pane_selected_line_i)

    def unmark_any_marked_items(self):
        self.marked_item_indices = []
