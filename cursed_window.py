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
        self.content_line_selected_i = 0
        self.lines_render_offset = 0

    # calculates the attributes for how the text should be rendered based on the text content
    def calculate_attributes(self, text):
        # ordinary files are bold
        text_attribute = curses.A_BOLD

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

    def render_line(self, screen_line_i):
        content_line_to_render_index = screen_line_i + self.lines_render_offset
        text = self.text_content[content_line_to_render_index]
        text_attribute = self.calculate_attributes(text)
        self.add_string(screen_line_i, text, text_attribute)

    def render_selected_line(self):
        logging.debug("rendering selected line at index: {}".format(self.content_line_selected_i))
        if self.content_line_selected_i < 0:
            return

        y_to_draw_at = (self.content_line_selected_i % len(self.text_content)) - self.lines_render_offset

        text = self.text_content[self.content_line_selected_i]
        text_attribute = self.calculate_attributes(text)

        text_attribute = text_attribute | curses.A_REVERSE

        self.add_string(y_to_draw_at, text, text_attribute)
        # fill the rest of the line after the last addition
        self.window.chgat(-1, text_attribute)

    def render(self, text_content, content_line_selected_i):
        self.text_content = text_content
        self.content_line_selected_i = content_line_selected_i
        last_screen_index = self.height - 1
        if self.content_line_selected_i >= last_screen_index + self.lines_render_offset:
            self.lines_render_offset = self.content_line_selected_i - last_screen_index
        elif self.content_line_selected_i <= self.lines_render_offset:
            self.lines_render_offset = self.content_line_selected_i

        number_lines = len(self.text_content)
        logging.debug("rendering {} lines".format(number_lines))
        max_line_to_render = min(number_lines, self.height)
        for screen_line_i in range(max_line_to_render):
            if screen_line_i != self.content_line_selected_i - self.lines_render_offset:
                self.render_line(screen_line_i)

        if number_lines > 0:
            self.render_selected_line()

    def render_without_selected(self, text_content):
        self.text_content = text_content
        number_lines = len(self.text_content)
        logging.debug("rendering {} lines".format(number_lines))
        max_line_to_render = min(number_lines, self.height)
        for line_i in range(max_line_to_render):
            self.render_line(line_i)

    def refresh(self):
        self.window.noutrefresh()
        curses.doupdate()

    def clear(self):
        self.window.clear()

