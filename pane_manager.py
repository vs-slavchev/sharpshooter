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

    def render_panes(self, left_lines, main_lines, right_lines,
                     left_selected, main_selected):
        self.left_window.set_text_content(left_lines)
        self.left_window.render()
        if len(left_lines) > 0:
            self.left_window.render_selected_line(left_selected)

        self.main_window.set_text_content(main_lines)
        self.main_window.render()
        self.main_window.render_selected_line(main_selected)

        self.right_window.set_text_content(right_lines)
        self.right_window.render()

    def refresh_panes(self):
        self.left_window.refresh()
        self.main_window.refresh()
        self.right_window.refresh()
