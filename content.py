"""
    Contains the state of the application - panes, current working directory, selected lines.
"""

import logging
import file_system
import platform_utils
import shutil
import threading
from collections import deque

from config_manager import ConfigManager
from fs_item import FsItem
import utility
from file_system_error import FileSystemError


class Content:
    def __init__(self, config_manager=None):
        self.parent_lines = []
        self.main_lines = []
        self.child_path = ""
        self.child_lines = []

        self.cwd = file_system.provide_initial_cwd()
        self.parent_pane_selected_line_i = 0
        self.main_pane_selected_line_i = 0

        self.paths_to_copy = []
        self.copy_removes_source = False

        self.marked_item_indices = []
        # newest last; once full, the oldest delete is forgotten
        self.trash_undo_stack = deque(maxlen=128)
        # set by background work when it finishes, so the UI redraws without waiting for a key
        self.background_changed = threading.Event()
        self._background_tasks = 0
        self._background_lock = threading.Lock()
        # the status line is written by background threads too
        self._status_lock = threading.RLock()
        # a name to put on the clipboard via the terminal, written by the main thread between screen updates
        self.pending_osc52_text = None

        # the status line: the user's latest action, plus a background result that arrived after it
        self._user_status = ""
        self._background_status = ""
        self.pending_zip_name = ""
        # only one zip or unzip at a time
        self.archive_busy = False

        self.config_manager = config_manager if config_manager is not None else ConfigManager()
        self.show_hidden = self.config_manager.get_show_hidden()
        self.show_hotkeys = self.config_manager.get_show_hotkeys()

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

        self.config_manager.set_config_settings_value('show_hidden', self.show_hidden)

    def toggle_hotkeys(self):
        logging.info("action: toggling hotkey guide from: {}".format(self.show_hotkeys))
        self.show_hotkeys = not self.show_hotkeys
        self.config_manager.set_config_settings_value('show_hotkeys', self.show_hotkeys)

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
        pane_content = file_system.list_all_in(path_to_folder)

        if not self.show_hidden:
            pane_content = list(filter(lambda fs_item: not fs_item.is_hidden(), pane_content))

        return pane_content

    def query_parent_pane_content(self):
        pane_content = file_system.list_all_in(self.parent_directory())

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
            self.run_in_background("Could not open [{}].".format(self.file_name_from_path(self.child_path)),
                                   file_system.open_file, self.child_path)

    def undo(self):
        logging.info("action: undo")
        if not self.trash_undo_stack:
            return
        trashed_name, original_path = self.trash_undo_stack.pop()
        file_name = self.file_name_from_path(original_path)
        try:
            file_system.restore_from_trash(trashed_name, original_path)
            self.describe_last_action("Undone delete of [{}].", file_name)
        except FileSystemError as e:
            if file_system.is_in_trash(trashed_name, original_path):
                # keep it for a later retry, but at the bottom so it does not block undoing older deletes
                self.trash_undo_stack.appendleft((trashed_name, original_path))
            self.describe_last_action("Could not restore [{}]: {}.", file_name, e.message)

    def delete(self):
        logging.info("action: delete")
        if self.no_main_lines_exist():
            return
        if self.exist_marked_items():
            paths_to_delete = self.get_paths_of_marked_items()
        else:
            paths_to_delete = [self.child_path]

        errors = []
        deleted = 0
        all_undoable = True
        for path in paths_to_delete:
            try:
                deletion_info = file_system.delete(path)
            except FileSystemError as e:
                if e.message not in errors:
                    errors.append(e.message)
                continue
            deleted += 1
            if deletion_info is None:
                all_undoable = False
            else:
                self.save_deletion_info(deletion_info)

        if len(paths_to_delete) == 1:
            what = "[{}]".format(self.file_name_from_path(paths_to_delete[0]))
        elif errors:
            what = "{} of {} files".format(deleted, len(paths_to_delete))
        else:
            what = "{} files".format(deleted)
        finder_note = "" if all_undoable else " (via Finder: restore from the Trash, undo is not available)"

        reasons = "; ".join(errors)
        if not errors:
            self.describe_last_action("Deleted {}{}.", what, finder_note)
        elif deleted == 0:
            self.describe_last_action("{}: {}.", reasons, what if len(paths_to_delete) == 1 else "no files deleted")
        else:
            self.describe_last_action("Deleted {}{}; the rest failed: {}.", what, finder_note, reasons)
        self.unmark_any_marked_items()
        self.main_pane_selected_line_i = min(self.main_pane_selected_line_i, len(self.main_lines) - 1)

    def save_deletion_info(self, deletion_info):
        """deletion_info is (name in trash, original path), as returned by file_system.delete."""
        self.trash_undo_stack.append(deletion_info)

    def make_new_folder(self, new_folder_name):
        logging.info("action: make new folder")
        try:
            file_system.make_new_folder(self.to_path(new_folder_name))
            self.recalculate_content()
            self.select_line_with(FsItem(new_folder_name + "/"))
            self.unmark_any_marked_items()
            self.describe_last_action("Made new folder [{}].", new_folder_name)
        except FileSystemError as e:
            self.describe_last_action("{}: [{}].", e.message, new_folder_name)

    def rename(self, new_name):
        logging.info("action: rename")
        if self.no_main_lines_exist():
            return
        old_path = self.to_path(self.currently_selected_item().text)
        new_path = self.to_path(new_name)
        try:
            file_system.rename(old_path, new_path)
            self.describe_last_action("Renamed [{}] to [{}].", self.file_name_from_path(old_path), new_name)
        except FileSystemError as e:
            self.describe_last_action("Could not rename [{}]: {}.", self.file_name_from_path(old_path), e.message)

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

        file_system_function = file_system.move if self.copy_removes_source else file_system.copy_paste
        try:
            for path in self.paths_to_copy:
                file_system_function(path, folder_to_paste_in)
        except FileSystemError as e:
            self.describe_last_action("Could not paste {} files: {}.", len(self.paths_to_copy), e.message)
            self.paths_to_copy = []
        else:
            self.recalculate_content()

            # select newly pasted file
            if len(self.paths_to_copy) == 1:
                newly_pasted_item = FsItem(utility.extract_item_name_from_path(self.paths_to_copy[0]))
                self.select_line_with(newly_pasted_item)
                self.describe_last_action("Pasted [{}].", newly_pasted_item.text)
            elif len(self.paths_to_copy) > 1:
                self.main_pane_selected_line_i = 0
                self.describe_last_action("Pasted {} files.", len(self.paths_to_copy))
        finally:
            self.paths_to_copy = []
            self.copy_removes_source = False
            self.unmark_any_marked_items()

    def zip_unzip(self):
        logging.info("action: zip unzip")
        if self.no_main_lines_exist():
            return
        if self.archive_busy:
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
        selected = self.currently_selected_item()
        path_to_process = self.to_path(selected.text)
        self.describe_last_action("Zip [{}].", selected.text)
        # a folder's contents go at the archive root, so unzipping recreates the folder
        self.perform_zip(selected.get_clean_name(), [path_to_process], contents_only=selected.is_folder())

    def zip_marked_items(self):
        logging.info("action: zip marked")
        self.describe_last_action("Zip {} files.", len(self.marked_item_indices))
        self.perform_zip('archive_{}'.format(utility.now()), self.get_paths_of_marked_items())
        self.unmark_any_marked_items()

    def perform_zip(self, wanted_name, paths, contents_only=False):
        # never overwrite an existing archive: claim a free name, so cleaning up after a failure is always safe
        try:
            zip_file_name = file_system.claim_unique_name(self.cwd, wanted_name, '.zip')
        except FileSystemError as e:
            self.describe_last_action("Could not zip: {}.", e.message)
            return
        self.archive_busy = True
        self.pending_zip_name = zip_file_name
        archive_path = self.to_path(zip_file_name + '.zip')

        def remove_partial_archive():
            file_system.remove_file(archive_path)

        def finished():
            self.pending_zip_name = ""
            self.archive_busy = False

        self.run_in_background("Zip of [{}] failed.".format(zip_file_name),
                               file_system.zip_items, paths, archive_path, contents_only,
                               on_failure=remove_partial_archive, on_finish=finished)

    def unzip(self, format_abbreviation):
        logging.info("action: unzip")
        currently_selected_text = self.currently_selected_item().text
        path_to_process = self.to_path(currently_selected_text)
        # always a new folder, claimed now: nothing the user already has is overwritten, a second unzip cannot
        # pick the same folder, and a failure can be cleaned up
        try:
            folder_name = file_system.claim_unique_name(
                self.cwd, currently_selected_text[:-len(format_abbreviation)], make_folder=True)
        except FileSystemError as e:
            self.describe_last_action("Could not unzip [{}]: {}.", currently_selected_text, e.message)
            return
        folder_to_unpack_in = self.to_path(folder_name)
        self.archive_busy = True

        def finished():
            self.archive_busy = False

        def remove_partial_folder():
            file_system.permanent_delete(folder_to_unpack_in)

        self.describe_last_action("Unzip [{}] into [{}/].", currently_selected_text, folder_name)
        self.run_in_background("Unzip of [{}] failed.".format(currently_selected_text),
                               shutil.unpack_archive, path_to_process, folder_to_unpack_in, 'zip',
                               on_failure=remove_partial_folder, on_finish=finished)

    def run_in_background(self, failure_text, work, *args, on_success=None, on_failure=None, on_finish=None):
        """Run work(*args) in a thread. A failure is shown on the status line instead of being lost:
        a FileSystemError's own message, otherwise failure_text. on_success gets work's result."""
        with self._status_lock:
            status_when_started = self._user_status

        def task():
            try:
                result = work(*args)
                if on_success is not None:
                    on_success(result, status_when_started)
            except Exception as e:
                if isinstance(e, FileSystemError):
                    failure = e.message + "."
                else:
                    logging.exception(e)
                    failure = failure_text
                self.report_from_background(status_when_started, failure)
                if on_failure is not None:
                    try:
                        on_failure()
                    except Exception as cleanup_error:  # never let cleanup print over the screen
                        logging.exception(cleanup_error)
            finally:
                if on_finish is not None:
                    on_finish()
                # flag first, then count down: the input loop never sees "nothing running, nothing changed"
                # while a result is still waiting to be drawn
                self.background_changed.set()
                with self._background_lock:
                    self._background_tasks -= 1

        with self._background_lock:
            self._background_tasks += 1
        threading.Thread(target=task).start()

    def report_from_background(self, status_when_started, text):
        """Show text, but if the user did something else meanwhile keep that newer message and add text after it."""
        with self._status_lock:
            if self._user_status and self._user_status != status_when_started:
                self._background_status = text
            else:
                self._user_status, self._background_status = text, ""

    @property
    def last_action_description(self):
        with self._status_lock:
            if self._background_status:
                return "{} | {}".format(self._user_status, self._background_status)
            return self._user_status

    def background_work_pending(self):
        """True while background work runs or has finished without the screen being redrawn yet."""
        with self._background_lock:
            return self._background_tasks > 0 or self.background_changed.is_set()

    def copy_name_to_clipboard(self):
        logging.info("action: copy name to clipboard")
        if self.no_main_lines_exist():
            return
        name = self.currently_selected_item().get_clean_name()

        def copied(confirmed, status_when_started):
            if confirmed:
                self.report_from_background(status_when_started, "Copied [{}] to clipboard.".format(name))
            else:
                self.pending_osc52_text = name  # the main thread sends it to the terminal

        self.describe_last_action("Copying [{}]...", name)
        self.run_in_background("Could not copy [{}].".format(name), file_system.copy_with_clipboard_tools, name,
                               on_success=copied)

    def send_pending_osc52(self):
        """Main thread only, between screen updates. Returns True if the status line changed."""
        name = self.pending_osc52_text
        if name is None:
            return False
        self.pending_osc52_text = None
        try:
            file_system.copy_via_osc52(name)
            self.describe_last_action("Sent [{}] to the terminal clipboard; if it is missing: {}.",
                                      name, platform_utils.clipboard_install_hint())
        except FileSystemError as e:
            self.describe_last_action("Could not copy [{}]: {}.", name, e.message)
        return True

    def open_new_terminal(self):
        self.run_in_background("Could not open a terminal.", file_system.open_new_terminal, self.cwd)

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

    def describe_last_action(self, pattern, *values):
        """pattern is always a fixed string from this file; anything variable (file names, error messages)
        must be passed in values, so braces in it can never break the formatting."""
        with self._status_lock:
            self._user_status, self._background_status = pattern.format(*values), ""

    def clear_last_action_description(self):
        with self._status_lock:
            self._user_status, self._background_status = "", ""
