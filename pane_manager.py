"""
    Controls the rendering of each pane and other UI elements.
"""

import logging
import curses

from cursed_window import CursedWindow
from curses.textpad import Textbox, rectangle


class PaneManager:
    def __init__(self, standard_screen):
        screen_height, screen_width = standard_screen.getmaxyx()
        logging.debug("screen size WxH: {}x{}".format(screen_width, screen_height))
        self.pane_width = screen_width // 3
        window_y = 1
        window_footer_height = 1
        pane_height = screen_height - window_y - window_footer_height

        self.left_window = CursedWindow(1, window_y, self.pane_width - 1, pane_height)
        self.main_window = CursedWindow(self.pane_width, window_y, self.pane_width, pane_height)
        self.right_window = CursedWindow(self.pane_width * 2, window_y, self.pane_width, pane_height)

        self.top_line_width = screen_width - 1
        self.top_line = curses.newwin(1, self.top_line_width, 0, 1)

    def render_panes(self, renderable_content):
        # todo
        # get 3 objs from this: all are of type array of FsItem, and pass those to the respective windows
        left_lines, main_lines, right_lines, left_selected, main_selected = renderable_content

        self.left_window.render(left_lines, left_selected)
        self.main_window.render(main_lines, main_selected)
        self.right_window.render_without_selected(right_lines)

    def render_top_line(self, cwd_path):
        self.top_line.addnstr(0, 0, cwd_path, self.top_line_width, curses.A_BOLD)

    def refresh_panes(self):
        self.left_window.refresh()
        self.main_window.refresh()
        self.right_window.refresh()
        self.top_line.refresh()

    def clear_panes(self):
        self.left_window.clear()
        self.main_window.clear()
        self.right_window.clear()
        self.top_line.clear()

    def render_input_textbox(self, y_position, placeholder=""):
        edit_window = curses.newwin(1, self.pane_width - 2, y_position + 1, self.pane_width + 1)
        text_attribute = self.main_window.calculate_attributes(placeholder)
        self.main_window.get_window().addnstr(y_position, 0, ">", 1, text_attribute)
        self.main_window.refresh()

        # rename folders without the slash at the end
        if placeholder.endswith("/"):
            placeholder = placeholder[:-1]

        edit_window.addstr(0, 0, placeholder.encode('utf-8'))
        box = Textbox(edit_window)

        box.edit()

        message = box.gather()
        return str(message.strip("',/\n "))
