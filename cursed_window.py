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
        self.selected_line_i = 0

    def set_text_content(self, text_content):
        self.text_content = text_content

    def set_selected_line_i(self, line_i):
        self.selected_line_i = line_i

    def get_selected_line_i(self):
        return self.selected_line_i

    def render_line(self, y, is_selected = False):
        text = self.text_content[y]
        # ordinary files are bold
        text_attribute = curses.A_BOLD

        # hidden files are normal font
        if chr(text[0] and not is_selected) == '.':
            text_attribute = curses.A_NORMAL

        # folders are also colored
        if chr(text[-1]) == '/':
            text_attribute = text_attribute | curses.color_pair(2)

        # selected line is reversed
        if is_selected:
            text_attribute = text_attribute | curses.A_REVERSE
    
        try:
            self.window.addnstr(y, 0, text, self.width, text_attribute)
        except curses.error:
            logging.error("cannot add str y={} text=\"{}\"".format(y, text))

        # fill the rest of the line after the last addition
        if is_selected:
            self.window.chgat(-1, text_attribute)
    def render(self):
        number_lines = len(self.text_content)
        max_line_to_render = min(number_lines, self.height)
        for line_i in range(max_line_to_render):
            self.render_line(line_i)

        self.render_line(self.selected_line_i , is_selected=True)

    def refresh(self):
        """
        refresh a specific window only
        if you need to refresh multiple
        windows it's better to noutrefresh()
        them and do one doupdate()
        """
        self.window.noutrefresh()
        curses.doupdate()

