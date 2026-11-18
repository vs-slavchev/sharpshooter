"""
    Handles the user input, calls the content to update and renders the new view in the UI.
"""

import curses
import logging

from input_keys import InputKeys
from pane_manager import PaneManager
from content import Content


class Controller:
    def __init__(self, standard_screen, config_manager):
        self.is_working = True
        self.standard_screen = standard_screen
        curses.curs_set(False)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.content = Content(config_manager)
        self.input_keys = InputKeys(config_manager)
        self.pane_manager = PaneManager(standard_screen)

        self.keys_to_actions = {
            self.input_keys.down_key: self.content.down,
            'KEY_DOWN': self.content.down,
            self.input_keys.up_key: self.content.up,
            'KEY_UP': self.content.up,
            self.input_keys.open_parent_key: self.content.open_parent,
            'KEY_LEFT': self.content.open_parent,
            self.input_keys.open_child_key: self.content.open_child,
            'KEY_RIGHT': self.content.open_child,
            self.input_keys.quit_key: self.quit,
            self.input_keys.open_terminal_key: self.content.open_new_terminal,
            self.input_keys.open_file: self.content.open_selected,
            self.input_keys.toggle_hidden: self.content.toggle_hidden,
            self.input_keys.delete: self.content.delete,
            self.input_keys.new_folder: self.make_new_folder,
            self.input_keys.rename: self.rename_selected,
            self.input_keys.copy: self.content.copy,
            self.input_keys.paste: self.content.paste,
            self.input_keys.cut: self.content.cut,
            self.input_keys.zip_unzip: self.content.zip_unzip,
            self.input_keys.mark_item: self.content.toggle_mark_item,
            self.input_keys.undo: self.content.undo,
            self.input_keys.toggle_hotkeys: self.content.toggle_hotkeys,
            self.input_keys.copy_name: self.content.copy_name_to_clipboard,
        }

    def run(self):
        while self.is_working:
            try:
                self.update()
            except Exception as e:
                logging.exception(e)
                raise

    def update(self):
        self.standard_screen.clear()
        self.pane_manager.clear_panes()

        self.content.recalculate_content()

        self.pane_manager.render_path_indicator(self.content.cwd)
        self.pane_manager.render_panes(self.content.get_renderable_content())
        self.pane_manager.render_last_action_description(self.content.last_action_description)
        if self.content.show_hotkeys:
            self.pane_manager.render_hotkey_guide(self.input_keys.hotkey_guide)

        self.standard_screen.refresh()
        self.pane_manager.refresh_panes()

        # writing to the terminal is only safe here, between screen updates on the main thread
        if self.content.send_pending_osc52():
            return  # redraw to show the result
        self.process_input()

    def process_input(self):
        input_key = self.wait_for_key()
        if input_key is None:
            return  # background work changed something: just redraw
        logging.info("input: {}".format(input_key))

        if input_key in self.keys_to_actions:
            action = self.keys_to_actions.get(input_key)
            action()

    def wait_for_key(self):
        """Return the next key, or None when background work finished and the screen should be redrawn."""
        while True:
            # while background work (zip, launching programs) runs, wake up regularly so its result shows
            # without a key press; otherwise just wait for the next key
            self.standard_screen.timeout(100 if self.content.background_work_pending() else -1)
            try:
                return self.standard_screen.getkey()
            except curses.error:  # timed out without a key
                if self.content.background_changed.is_set():
                    self.content.background_changed.clear()
                    return None

    def quit(self):
        self.is_working = False

    def make_new_folder(self):
        new_folder_name = self.pane_manager.render_create_folder_input_textbox(self.content.get_num_main_lines())
        if new_folder_name is not None:
            self.content.make_new_folder(new_folder_name)

    def rename_selected(self):
        if self.content.no_main_lines_exist():
            return
        new_name = self.pane_manager.render_rename_input_textbox(
            self.content.get_main_selected_line_i(),
            self.content.currently_selected_item())
        if new_name is not None:
            self.content.rename(new_name)
