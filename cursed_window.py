import curses

class CursedWindow:

    def __init__(self, x, y, width, height):
        """
        0,0 is top-left
        """
        self.window =  curses.newwin(height, width, y, x)
        self.x = x
        self.y = y
        self.width = width
        self.hegith = height
        self.text_content = []

    def set_text_content(self, text_content):
        self.text_content = text_content

    def render_line(self, y, is_selected = False):
        text = self.text_content[y]
        self.window.addstr(y, 0, text)

    def render(self):
        for line_i in range(len(self.text_content)):
            self.render_line(line_i)

        self.render_line(1, is_selected=True)

    def refresh(self):
        """
        refresh a specific window only
        if you need to refresh multiple
        windows it's better to noutrefresh()
        them and do one doupdate()
        """
        self.window.noutrefresh()
        curses.doupdate()

