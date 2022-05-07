"""
    Handles the user input, calls the content to update and renders the new view in the UI.
"""

import curses
import logging

from input_keys import InputKeys
from pane_manager import PaneManager
from content import Content


class Controller:
    def __init__(self, standard_screen):
        self.is_working = True
        self.standard_screen = standard_screen
        curses.curs_set(False)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.content = Content()
        self.input_keys = InputKeys()
        self.pane_manager = PaneManager(standard_screen)

    def run(self):
        while self.is_working:
            try:
                self.update()
            except Exception as e:
                # todo log traceback too
                logging.error(e)
                # todo raise only when in debug
                raise

    def update(self):
        self.standard_screen.clear()
        self.pane_manager.clear_panes()

        self.content.recalculate_content()

        self.pane_manager.render_path_indicator(self.content.cwd)
        self.pane_manager.render_panes(self.content.get_renderable_content())
        self.pane_manager.render_last_action_description(self.content.last_action_description)
        self.pane_manager.render_hotkey_guide(self.input_keys.hotkey_guide)

        self.standard_screen.refresh()
        self.pane_manager.refresh_panes()

        self.process_input()

    def process_input(self):
        input_key = self.standard_screen.getkey()
        logging.info("input: {}".format(input_key))
        if input_key == self.input_keys.down_key or input_key == 'KEY_DOWN':
            self.content.down()
        elif input_key == self.input_keys.up_key or input_key == 'KEY_UP':
            self.content.up()
        elif input_key == self.input_keys.open_parent_key or input_key == 'KEY_LEFT':
            self.content.open_parent()
        elif input_key == self.input_keys.open_child_key or input_key == 'KEY_RIGHT':
            self.content.open_child()
        elif input_key == self.input_keys.quit_key:
            self.is_working = False
        elif input_key == self.input_keys.open_terminal_key:
            self.content.open_new_terminal()
        elif input_key == self.input_keys.open_file:
            self.content.open_selected()
        elif input_key == self.input_keys.toggle_hidden:
            self.content.toggle_show_hidden()
        elif input_key == self.input_keys.delete:
            self.content.delete()
        elif input_key == self.input_keys.new_folder:
            self.make_new_folder()
        elif input_key == self.input_keys.rename:
            self.rename_selected()
        elif input_key == self.input_keys.copy:
            self.content.copy()
        elif input_key == self.input_keys.paste:
            self.content.paste()
        elif input_key == self.input_keys.cut:
            self.content.cut()
        elif input_key == self.input_keys.zip_unzip:
            self.content.zip_unzip()
        elif input_key == self.input_keys.mark_item:
            self.content.toggle_mark_item()
        elif input_key == self.input_keys.undo:
            self.content.undo()

    def make_new_folder(self):
        new_folder_name = self.pane_manager.render_create_folder_input_textbox(self.content.get_num_main_lines())
        self.content.make_new_folder(new_folder_name)

    def rename_selected(self):
        if self.content.no_main_lines_exist():
            return
        new_name = self.pane_manager.render_rename_input_textbox(
            self.content.get_main_selected_line_i(),
            self.content.currently_selected_item())
        self.content.rename(new_name)
