import curses
import logging


class CursedWindow:

    def __init__(self, x, y, width, height):
        """
        0,0 is top-left
        """
        self.window =  curses.newwin(height, width, y, x)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text_content = []

    def set_text_content(self, text_content):
        self.text_content = text_content

    def calculate_attributes(self, text):
        # ordinary files are bold
        text_attribute = curses.A_BOLD

        # hidden files are normal font
        if chr(text[0]) == '.':
            text_attribute = curses.A_NORMAL

        # folders are also colored
        if chr(text[-1]) == '/':
            text_attribute = text_attribute | curses.color_pair(2)

        return text_attribute

    def add_string(self, y, text, text_attribute):
        try:
            self.window.addnstr(y, 0, text, self.width, text_attribute)
        except curses.error:
            logging.error("cannot add str y={} text=\"{}\"".format(y, text))

    def render_line(self, y):
        text = self.text_content[y]
        text_attribute = self.calculate_attributes(text)
        self.add_string(y, text, text_attribute)

    def render_selected_line(self, selected_index):
        logging.debug("rendering selected line: {}".format(selected_index))
        selected_index = selected_index % len(self.text_content)

        text = self.text_content[selected_index]
        text_attribute = self.calculate_attributes(text)

        text_attribute = text_attribute | curses.A_REVERSE

        self.add_string(selected_index, text, text_attribute)
        # fill the rest of the line after the last addition
        self.window.chgat(-1, text_attribute)

    def render(self):
        number_lines = len(self.text_content)
        max_line_to_render = min(number_lines, self.height)
        for line_i in range(max_line_to_render):
            self.render_line(line_i)

    def refresh(self):
        self.window.noutrefresh()
        curses.doupdate()

