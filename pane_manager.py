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
        pane_height = screen_height - window_y

        self.left_window = CursedWindow(1, window_y, self.pane_width - 1, pane_height)
        self.main_window = CursedWindow(self.pane_width, window_y, self.pane_width, pane_height)
        self.right_window = CursedWindow(self.pane_width * 2, window_y, self.pane_width, pane_height)

        self.top_line_width = screen_width - 1
        self.top_line = curses.newwin(1, self.top_line_width, 0, 1)

    def render_panes(self, renderable_content):
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

    def render_new_folder_input_textbox(self, num_main_lines):
        y_parent_relative = num_main_lines - 1
        edit_window_y = y_parent_relative + 2
        edit_window = curses.newwin(1, self.pane_width - 2, edit_window_y, self.pane_width + 1)
        parent_window = self.main_window.get_window()
        try:
            rectangle(parent_window, y_parent_relative, 0, y_parent_relative + 2, self.pane_width - 1)
        except curses.error:
            pass
        parent_window.refresh()

        box = Textbox(edit_window)

        # Let the user edit until Ctrl-G is struck.
        box.edit()

        # Get resulting contents
        message = box.gather()
        return str(message.strip("',/\n "))
