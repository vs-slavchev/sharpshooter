
import curses
import logging
import utility


class SingleLineWindow:
    def __init__(self, x, y, width, text_attribute):
        self.width = width
        self.text_attribute = text_attribute
        self.bottom_window = curses.newwin(1, width, y, x)

    def render(self, text):
        text = utility.fit_text_to_line_length(self.width, text)
        self.bottom_window.addnstr(0, 0, text, len(text), self.text_attribute)

    def refresh(self):
        self.bottom_window.noutrefresh()

    def clear(self):
        self.bottom_window.clear()
