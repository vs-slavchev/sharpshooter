import curses
import logging


class CursedWindow:

    def __init__(self, x, y, width, height):
        """
        0,0 is top-left
        """
        self.window = curses.newwin(height, width, y, x)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text_content = []
        self.lines_render_offset = 0

    def get_window(self):
        return self.window

    def render(self, text_content, content_line_selected_i):
        self.text_content = text_content
        last_screen_index = self.height - 1
        selected_line_is_below_screen = content_line_selected_i >= last_screen_index + self.lines_render_offset
        selected_line_is_above_screen = content_line_selected_i <= self.lines_render_offset
        if selected_line_is_below_screen:
            self.lines_render_offset = content_line_selected_i - last_screen_index
        elif selected_line_is_above_screen:
            self.lines_render_offset = content_line_selected_i

        number_lines = len(self.text_content)
        logging.debug("rendering {} lines".format(number_lines))
        max_line_to_render = min(number_lines, self.height)
        for screen_line_i in range(max_line_to_render):
            if screen_line_i != content_line_selected_i - self.lines_render_offset:
                self.render_line(screen_line_i)

        if number_lines > 0:
            self.render_selected_line(content_line_selected_i)

    def render_without_selected(self, text_content):
        self.text_content = text_content
        number_lines = len(self.text_content)
        logging.debug("rendering {} lines".format(number_lines))
        max_line_to_render = min(number_lines, self.height)
        for line_i in range(max_line_to_render):
            self.render_line(line_i)

    def render_line(self, screen_line_i):
        content_line_to_render_index = screen_line_i + self.lines_render_offset
        try:
            text = self.text_content[content_line_to_render_index]
        except IndexError as index_error:
            logging.error(index_error)
            return
        text_attribute = self.calculate_attributes(text)
        self.add_string(screen_line_i, text, text_attribute)

    # calculates the attributes for how the text should be rendered based on the text content
    def calculate_attributes(self, text):
        # ordinary files are bold
        text_attribute = curses.A_BOLD

        if len(text) == 0:
            return text_attribute

        # hidden files are normal font
        if text[0] == '.':
            text_attribute = curses.A_NORMAL

        # folders are also colored
        if text[-1] == '/':
            text_attribute = text_attribute | curses.color_pair(2)

        return text_attribute

    def add_string(self, y, text, text_attribute):
        text = " " + text
        try:
            self.window.addnstr(y, 0, text, self.width, text_attribute)
        except curses.error:
            logging.error("cannot add str text=\"{}\" at y={} ".format(text, y))

    def render_selected_line(self, content_line_selected_i):
        logging.debug("rendering selected line at index: {}".format(content_line_selected_i))
        if content_line_selected_i < 0:
            return

        y_to_draw_at = (content_line_selected_i % len(self.text_content)) - self.lines_render_offset

        text = self.text_content[content_line_selected_i]
        text_attribute = self.calculate_attributes(text)

        text_attribute = text_attribute | curses.A_REVERSE

        self.add_string(y_to_draw_at, text, text_attribute)
        # fill the rest of the line after the last addition
        self.window.chgat(-1, text_attribute)

    def refresh(self):
        self.window.noutrefresh()
        curses.doupdate()

    def clear(self):
        self.window.clear()

