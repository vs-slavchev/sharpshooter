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

    def update(self):
        while self.is_working:
            self.standard_screen.clear()
            self.pane_manager.clear_panes()

            self.content.recalculate_content()

            self.pane_manager.render_top_line(self.content.cwd)
            self.pane_manager.render_panes(self.content.get_renderable_content())

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
        elif input_key == self.input_keys.toggle_show_hidden:
            self.content.toggle_show_hidden()
        elif input_key == self.input_keys.delete:
            self.content.delete_selected()
        elif input_key == self.input_keys.make_new_folder:
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
        elif input_key == self.input_keys.toggle_mark_item:
            self.content.toggle_mark_item()

    def make_new_folder(self):
        y_position = self.pane_manager.main_window\
                         .calculate_max_line_to_render(self.content.get_num_main_lines() - 1) + 1
        new_folder_name = self.pane_manager.render_input_textbox(y_position)
        self.content.make_new_folder(new_folder_name)

    # todo fix bug: use index in the rendered view and not in the items list
    def rename_selected(self):
        if self.content.no_main_lines_exist():
            return
        new_name = self.pane_manager.render_input_textbox(
            self.content.get_main_selected_line_i(), self.content.currently_selected_item())
        self.content.rename(self.content.currently_selected_item().text, new_name)
