import logging

from cursed_window import CursedWindow


class PaneManager:
    def __init__(self, standard_screen):
        screen_height, screen_width = standard_screen.getmaxyx()
        logging.debug("screen size WxH: {}x{}".format(screen_width, screen_height))
        window_width = screen_width // 3
        window_y = 1
        window_height = screen_height - window_y

        self.left_window = CursedWindow(1, window_y, window_width - 1, window_height)
        self.main_window = CursedWindow(window_width, window_y, window_width, window_height)
        self.right_window = CursedWindow(window_width * 2, window_y, window_width, window_height)

    def render_panes(self, renderable_content):
        left_lines, main_lines, right_lines, left_selected, main_selected = renderable_content

        self.left_window.render(left_lines, left_selected)
        self.main_window.render(main_lines, main_selected)
        self.right_window.render(right_lines)

    def refresh_panes(self):
        self.left_window.refresh()
        self.main_window.refresh()
        self.right_window.refresh()

    def clear_panes(self):
        self.left_window.clear()
        self.main_window.clear()
        self.right_window.clear()
