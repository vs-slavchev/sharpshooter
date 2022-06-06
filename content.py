"""
    Contains the state of the application - panes, current working directory, selected lines.
"""

import logging
import file_system
import shutil
import threading
from queue import LifoQueue

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

        self.paths_to_copy = []
        self.copy_removes_source = False

        self.marked_item_indices = []
        self.deleted_original_file_paths_queue = LifoQueue(maxsize=128)

        self.last_action_description = ""
        self.pending_zip_name = ""

        self.config_manager = ConfigManager()
        self.show_hidden = self.config_manager.get_show_hidden()

        self.recalculate_content()

    def toggle_hidden(self):
        logging.info("action: toggling hide/show hidden files from: {}".format(self.show_hidden))
        self.show_hidden = not self.show_hidden

        if self.no_main_lines_exist():
            return
        if not self.currently_selected_item().is_hidden():
            self.recalculate_same_selected_line()
        else:
            self.select_closest_to_hidden_item()

        # save change to the config file
        value_to_write = str(self.show_hidden)
        self.config_manager.set_config_settings_value('show_hidden', value_to_write)

    # the position of the selected line might change if items before it are hidden, but we want the same item
    # to be selected after either hiding or showing
    def recalculate_same_selected_line(self):
        marked_fs_items = self.get_marked_items()
        selected_item = self.currently_selected_item()

        self.main_lines = self.query_pane_content(self.cwd)

        self.select_line_with(selected_item)
        self.repopulate_marked_item_indices(marked_fs_items)

    # hiding a hidden item; only happens when hiding because only then can a hidden item be selected
    def select_closest_to_hidden_item(self):
        marked_fs_items = self.get_marked_items()
        from_selected_to_start = list(range(self.main_pane_selected_line_i - 1, 0, -1))
        from_selected_to_end = list(range(self.main_pane_selected_line_i + 1, len(self.main_lines) - 1, 1))
        indices_to_iterate = from_selected_to_start + from_selected_to_end
        closest_visible_fs_item = None
        for fs_item_i in indices_to_iterate:
            fs_item = self.main_lines[fs_item_i]
            if not fs_item.is_hidden():
                closest_visible_fs_item = fs_item
                break

        self.main_lines = self.query_pane_content(self.cwd)

        self.select_line_with(closest_visible_fs_item)
        self.repopulate_marked_item_indices(marked_fs_items)

    # repopulate the marked item indices list by mapping marked fs items back to an index if they are still visible
    def repopulate_marked_item_indices(self, marked_fs_items):
        self.unmark_any_marked_items()
        self.marked_item_indices = [self.main_lines.index(mi) for mi in marked_fs_items if mi in self.main_lines]

    # returns the lines that represent the files and folders in the path_to_folder
    def query_pane_content(self, path_to_folder):
        pane_content = terminal.list_all_in(path_to_folder)

        if not self.show_hidden:
            pane_content = list(filter(lambda fs_item: not fs_item.is_hidden(), pane_content))

        return pane_content

    def query_parent_pane_content(self):
        pane_content = terminal.list_all_in(self.parent_directory())

        if not self.show_hidden:
            selected_parent_item = self.get_parent_folder()
            pane_content = list(filter(
                lambda fs_item: not fs_item.is_hidden() or fs_item.text == selected_parent_item, pane_content))

        return pane_content

    def recalculate_content(self):
        self.parent_lines = self.query_parent_pane_content()
        self.main_lines = self.query_pane_content(self.cwd)
        self.child_path = ""
        self.child_lines = []
        if len(self.main_lines) > 0:
            self.child_path = self.to_path(self.currently_selected_item().text)
            if utility.is_folder(self.child_path):
                self.child_lines = self.query_pane_content(self.child_path)
            else:
                self.child_lines = []
        if self.cwd == "/":
            self.parent_lines = []
        else:
            parent_folder = self.get_parent_folder()
            logging.info("parent folder: {}".format(parent_folder))
            self.parent_pane_selected_line_i = list(map(lambda pl: pl.text, self.parent_lines)).index(parent_folder)

    def get_parent_folder(self):
        path_elements = self.to_path_elements(self.cwd)
        if len(path_elements) > 0:
            return path_elements[-1] + "/"
        else:
            return ""

    def open_parent(self):
        logging.info("action: open_parent")
        there_is_some_parent = len(self.to_path_elements(self.cwd)) > 0
        if there_is_some_parent:
            self.set_cwd_to_parent_directory()
            self.unmark_any_marked_items()
            self.clear_last_action_description()

    def currently_selected_item(self):
        if self.main_pane_selected_line_i >= len(self.main_lines):
            self.main_pane_selected_line_i = len(self.main_lines) - 1
        if self.main_pane_selected_line_i < 0:
            self.main_pane_selected_line_i = 0
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
        selected_is_openable_folder = child_exists and self.currently_selected_item().is_folder()
        if selected_is_openable_folder:
            self.main_pane_selected_line_i = 0
            self.cwd = self.child_path
            self.unmark_any_marked_items()
            self.clear_last_action_description()

    def parent_directory(self):
        higher_path_elements = self.get_higher_path_elements()
        if len(higher_path_elements) > 0:
            return "/" + "/".join(higher_path_elements) + "/"
        else:
            return "/"

    def get_higher_path_elements(self):
        only_path_elements = self.to_path_elements(self.cwd)
        higher_path_elements = only_path_elements[:-1]  # drop last path element
        return higher_path_elements

    def to_path_elements(self, full_path):
        higher_folders = full_path.split("/")
        only_path_elements = list(filter(lambda path_elem: len(path_elem) > 0, higher_folders))
        return only_path_elements

    def get_renderable_content(self):
        self.indicate_pending_zip()

        for marked_index in self.marked_item_indices:
            self.main_lines[marked_index].is_marked = True

        return self.parent_lines, \
            self.main_lines, \
            self.child_lines, \
            self.parent_pane_selected_line_i, \
            self.main_pane_selected_line_i

    def indicate_pending_zip(self):
        item_zipped = FsItem(self.pending_zip_name + ".zip")
        if not self.pending_zip_name == "" and item_zipped in self.main_lines:
            pending_zip_i = self.main_lines.index(item_zipped)
            self.main_lines[pending_zip_i].text = "[zipping...] " + self.main_lines[pending_zip_i].text

    def open_selected(self):
        if self.no_main_lines_exist():
            return
        if self.currently_selected_item().is_folder():
            self.open_child()
        else:
            terminal.open_file(self.child_path)

    def undo(self):
        logging.info("action: undo")
        if not self.deleted_original_file_paths_queue.empty():
            file_path = self.deleted_original_file_paths_queue.get()
            file_name = self.file_name_from_path(file_path)
            path_in_trash = terminal.get_users_trash_path() + file_name
            terminal.move(path_in_trash, file_path)
            self.describe_last_action("Undone delete of [{}].", file_name)

    def delete(self):
        logging.info("action: delete")
        if self.no_main_lines_exist():
            return
        if self.exist_marked_items():
            paths_to_delete = self.get_paths_of_marked_items()
            for path in paths_to_delete:
                self.save_deletion_info(terminal.delete(path))
            self.describe_last_action("Deleted {} files.", len(paths_to_delete))
        else:
            self.save_deletion_info(terminal.delete(self.child_path))
            self.describe_last_action("Deleted [{}].", self.file_name_from_path(self.child_path))
        self.unmark_any_marked_items()
        self.main_pane_selected_line_i = min(self.main_pane_selected_line_i, len(self.main_lines) - 1)

    def save_deletion_info(self, deleted_path):
        self.deleted_original_file_paths_queue.put(deleted_path)

    def make_new_folder(self, new_folder_name):
        logging.info("action: make new folder")
        if terminal.make_new_folder(self.to_path(new_folder_name)):
            self.recalculate_content()
            self.select_line_with(FsItem(new_folder_name + "/"))
            self.unmark_any_marked_items()
            self.describe_last_action("Made new folder [{}].", new_folder_name)
        else:
            self.describe_last_action("Already exists: [{}].", new_folder_name)

    def rename(self, new_name):
        logging.info("action: rename")
        if self.no_main_lines_exist():
            return
        old_path = self.to_path(self.currently_selected_item().text)
        new_path = self.to_path(new_name)
        terminal.move(old_path, new_path)
        self.describe_last_action("Renamed [{}] to [{}].", self.file_name_from_path(old_path), new_name)

    def copy(self):
        logging.info("action: copy")
        if self.no_main_lines_exist():
            return
        self.prepare_paths_to_copy()
        self.copy_removes_source = False
        logging.info("copy clipboard: {}".format(self.paths_to_copy))

    def cut(self):
        logging.info("action: cut")
        if self.no_main_lines_exist():
            return
        self.prepare_paths_to_copy()
        self.copy_removes_source = True
        logging.info("cut clipboard: {}".format(self.paths_to_copy))

    def prepare_paths_to_copy(self):
        if self.exist_marked_items():
            self.paths_to_copy = self.get_paths_of_marked_items()
            self.describe_last_action("Clipboard: {} files.", len(self.paths_to_copy))
        else:
            self.paths_to_copy = [self.child_path]
            self.describe_last_action("Clipboard: [{}].", self.file_name_from_path(self.child_path))

    def paste(self):
        logging.info("action: paste")
        if len(self.paths_to_copy) == 0:
            return
        folder_to_paste_in = self.cwd

        terminal_function = terminal.move if self.copy_removes_source else terminal.copy_paste
        for path in self.paths_to_copy:
            terminal_function(path, folder_to_paste_in)

        self.recalculate_content()

        # select newly copied file
        if len(self.paths_to_copy) == 1:
            newly_pasted_item = FsItem(utility.extract_item_name_from_path(self.paths_to_copy[0]))
            self.select_line_with(newly_pasted_item)
            self.describe_last_action("Pasted [{}].", newly_pasted_item.text)
        else:
            self.main_pane_selected_line_i = 0
            self.describe_last_action("Pasted {} files.", len(self.paths_to_copy))

        self.paths_to_copy = []
        self.copy_removes_source = False
        self.unmark_any_marked_items()

    def zip_unzip(self):
        logging.info("action: zip unzip")
        if self.no_main_lines_exist():
            return
        if not self.pending_zip_name == "":
            return

        format_abbreviation = ".zip"
        if self.currently_selected_item().text.endswith(format_abbreviation):
            self.unzip(format_abbreviation)
        else:
            if self.exist_marked_items():
                self.zip_marked_items()
            else:
                self.zip_selected_item()

    def zip_selected_item(self):
        logging.info("action: zip selected")
        path_to_process = self.to_path(self.currently_selected_item().text)
        zip_file_name = self.currently_selected_item().get_clean_name()
        self.perform_zip(path_to_process, zip_file_name)
        self.describe_last_action("Zip [{}].", self.currently_selected_item().text)

    def zip_marked_items(self):
        logging.info("action: zip marked")
        temp_marked_files_folder_name = 'temp_marked_files_folder/'
        temp_folder_path = self.to_path(temp_marked_files_folder_name)
        terminal.make_new_folder(temp_folder_path)
        for marked_path in self.get_paths_of_marked_items():
            terminal.copy_paste(marked_path, temp_folder_path)
        path_to_process = temp_folder_path
        zip_file_name = 'archive_{}'.format(utility.now())
        self.perform_zip(path_to_process, zip_file_name)
        terminal.permanent_delete(temp_folder_path)

        self.describe_last_action("Zip {} files.", len(self.marked_item_indices))
        self.unmark_any_marked_items()

    def perform_zip(self, path_to_process, zip_file_name):
        thread = threading.Thread(target=self.zip_in_thread,
                                  args=(zip_file_name, path_to_process,))
        thread.start()

    def zip_in_thread(self, zip_file_name, path_to_process):
        self.pending_zip_name = zip_file_name
        # the resulting file will have .zip appended to its name by the util function
        shutil.make_archive(self.to_path(zip_file_name), 'zip', path_to_process)
        self.pending_zip_name = ""

    def unzip(self, format_abbreviation):
        logging.info("action: unzip")
        currently_selected_text = self.currently_selected_item().text
        path_to_process = self.to_path(currently_selected_text)
        folder_to_unpack_in = self.to_path(currently_selected_text[:-len(format_abbreviation)])
        thread = threading.Thread(target=shutil.unpack_archive,
                                  args=(path_to_process, folder_to_unpack_in, 'zip'))
        thread.start()
        self.describe_last_action("Unzip [{}].", self.currently_selected_item().text)

    def open_new_terminal(self):
        terminal.open_new_terminal(self.cwd)

    def toggle_mark_item(self):
        logging.info("action: mark item")
        if self.no_main_lines_exist():
            return
        is_already_marked = self.main_pane_selected_line_i in self.marked_item_indices
        if is_already_marked:
            self.marked_item_indices.remove(self.main_pane_selected_line_i)
        else:
            self.marked_item_indices.append(self.main_pane_selected_line_i)

    def exist_marked_items(self):
        return len(self.marked_item_indices) > 0

    def get_num_main_lines(self):
        return len(self.main_lines)

    def get_main_selected_line_i(self):
        return self.main_pane_selected_line_i

    def select_line_with(self, fs_item):
        if not fs_item:
            return
        if fs_item.is_hidden() and not self.show_hidden:
            return
        try:
            self.main_pane_selected_line_i = self.main_lines.index(fs_item)
        except ValueError:
            logging.debug("Error selecting line {}".format(fs_item.text))

    def get_marked_items(self):
        return list(map(lambda mii: self.main_lines[mii], self.marked_item_indices))

    def get_paths_of_marked_items(self):
        return list(map(lambda mii: self.to_path(self.main_lines[mii].text), self.marked_item_indices))

    def unmark_any_marked_items(self):
        self.marked_item_indices = []

    def no_main_lines_exist(self):
        return len(self.main_lines) <= 0

    def to_path(self, fs_item_name):
        return self.cwd + fs_item_name

    def file_name_from_path(self, full_path):
        return self.to_path_elements(full_path)[-1]

    def describe_last_action(self, pattern, value, second_value=""):
        self.last_action_description = pattern.format(value, second_value)

    def clear_last_action_description(self):
        self.last_action_description = ""
