import curses
import logging

import terminal
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

            self.pane_manager.render_top_line(self.content.get_cwd())
            self.pane_manager.render_panes(self.content.get_renderable_content())

            self.standard_screen.refresh()
            self.pane_manager.refresh_panes()

            self.process_input()

    def process_input(self):
        input_key = self.standard_screen.getkey()
        logging.info("input: {}".format(input_key))
        if input_key == self.input_keys.down_key:
            self.content.down()
        elif input_key == self.input_keys.up_key:
            self.content.up()
        elif input_key == self.input_keys.open_parent_key:
            self.content.open_parent()
        elif input_key == self.input_keys.open_child_key:
            self.content.open_child()
        elif input_key == self.input_keys.quit_key:
            self.is_working = False
        elif input_key == self.input_keys.open_terminal_key:
            terminal.open_new_terminal(self.cwd)
        elif input_key == self.input_keys.open_file:
            terminal.open_file(self.content.get_child_path())
        elif input_key == self.input_keys.toggle_show_hidden:
            self.content.toggle_show_hidden()
        elif input_key == self.input_keys.delete:
            self.content.delete_selected()
        elif input_key == self.input_keys.make_new_folder:
            new_folder_name = self.pane_manager.render_new_folder_input_textbox(self.content.get_num_main_lines())
            self.content.make_new_folder(new_folder_name)
