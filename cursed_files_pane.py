"""
    A single pane that is rendered with the curses library.
"""

import curses
import logging


class CursedFilesPane:

    def __init__(self, x, y, width, height):
        """
        0,0 is top-left
        """
        self.window = curses.newwin(height, width, y, x)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fs_content = []
        self.lines_render_offset = 0

    def get_window(self):
        return self.window

    def render(self, fs_content, content_line_selected_i):
        self.fs_content = fs_content
        last_window_line_index = self.height - 2
        selected_line_is_below_screen = content_line_selected_i >= last_window_line_index + self.lines_render_offset
        selected_line_is_above_screen = content_line_selected_i <= self.lines_render_offset
        if selected_line_is_below_screen:
            self.lines_render_offset = content_line_selected_i - last_window_line_index
        elif selected_line_is_above_screen:
            self.lines_render_offset = content_line_selected_i

        number_lines = len(self.fs_content)
        logging.debug("rendering {} lines".format(number_lines))
        for screen_line_i in range(self.calculate_max_line_to_render(number_lines) + 1):
            if screen_line_i != content_line_selected_i - self.lines_render_offset:
                self.render_line(screen_line_i)

        if number_lines > 0:
            self.render_selected_line(content_line_selected_i)

    def render_without_selected(self, fs_content):
        self.fs_content = fs_content
        number_lines = len(self.fs_content)
        logging.debug("rendering {} lines".format(number_lines))
        for line_i in range(self.calculate_max_line_to_render(number_lines)):
            self.render_line(line_i)

    def calculate_max_line_to_render(self, number_lines):
        max_line_to_render = min(number_lines, self.height - 2)
        return max_line_to_render

    def render_line(self, screen_line_i):
        content_line_to_render_index = screen_line_i + self.lines_render_offset
        try:
            fs_item = self.fs_content[content_line_to_render_index]
        except IndexError as index_error:
            logging.error("cannot render line: {}".format(index_error))
            return
        text_attribute = self.calculate_attributes(fs_item)
        self.add_string(screen_line_i, fs_item.text, text_attribute)

    # calculates the attributes for how the text should be rendered based on the text content
    def calculate_attributes(self, fs_item):
        text = fs_item.text
        # ordinary files are bold
        text_attribute = curses.A_BOLD

        if len(text) == 0:
            return text_attribute

        # hidden files are normal font
        if text[0] == '.':
            text_attribute = curses.A_NORMAL

        if fs_item.is_marked:
            text_attribute = text_attribute | curses.A_UNDERLINE

        # folders are also colored
        if text[-1] == '/':
            text_attribute = text_attribute | curses.color_pair(2)

        return text_attribute

    def add_string(self, y, text, text_attribute):
        unused_chars_on_line = 2
        indicator_long_line = "..."
        text = " " + text
        if len(text) > self.width - unused_chars_on_line:
            last_char_index = self.width - (unused_chars_on_line + len(indicator_long_line))
            text = text[:last_char_index] + indicator_long_line

        try:
            self.window.addnstr(y, 0, text, self.width, text_attribute)
        except curses.error:
            logging.error("cannot add str text=\"{}\" at y={} ".format(text, y))

    def render_selected_line(self, content_line_selected_i):
        logging.debug("rendering selected line at index: {}".format(content_line_selected_i))
        if content_line_selected_i < 0:
            return

        y_to_draw_at = (content_line_selected_i % len(self.fs_content)) - self.lines_render_offset

        text_attribute = self.calculate_attributes(self.fs_content[content_line_selected_i])

        text_attribute = text_attribute | curses.A_REVERSE

        self.add_string(y_to_draw_at, self.fs_content[content_line_selected_i].text, text_attribute)
        # fill the rest of the line after the last addition
        self.window.chgat(-1, text_attribute)

    def refresh(self):
        self.window.noutrefresh()
        curses.doupdate()

    def clear(self):
        self.window.clear()

