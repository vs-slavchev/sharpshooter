"""
    Controls the rendering of each pane and other UI elements.
"""

import logging
import curses

import utility
from cursed_files_pane import CursedFilesPane
from curses.textpad import Textbox
from single_line_window import SingleLineWindow
from fs_item import FsItem


class PaneManager:
    def __init__(self, standard_screen):
        screen_height, screen_width = standard_screen.getmaxyx()
        logging.debug("screen size WxH: {}x{}".format(screen_width, screen_height))
        self.pane_width = screen_width // 3
        window_y = 1
        window_footer_height = 1
        pane_height = screen_height - window_y - window_footer_height

        self.left_window = CursedFilesPane(1, window_y, self.pane_width - 1, pane_height)
        self.main_window = CursedFilesPane(self.pane_width, window_y, self.pane_width, pane_height)
        self.right_window = CursedFilesPane(self.pane_width * 2, window_y, self.pane_width, pane_height)

        line_width = screen_width - 1
        self.path_indicator = SingleLineWindow(1, 0, line_width, curses.A_BOLD)
        self.last_action_description = SingleLineWindow(1, screen_height - 2, line_width, curses.A_NORMAL)
        self.hotkey_guide = SingleLineWindow(1, screen_height - 1, line_width, curses.A_NORMAL)

    def render_panes(self, renderable_content):
        left_lines, main_lines, right_lines, left_selected, main_selected = renderable_content

        self.left_window.render(left_lines, left_selected)
        self.main_window.render(main_lines, main_selected)
        self.right_window.render_without_selected(right_lines)

    def render_path_indicator(self, cwd_path):
        self.path_indicator.render(cwd_path)

    def render_last_action_description(self, last_action_description):
        self.last_action_description.render(last_action_description)

    def render_hotkey_guide(self, hotkey_guide):
        self.hotkey_guide.render(hotkey_guide)

    def refresh_panes(self):
        self.left_window.refresh()
        self.main_window.refresh()
        self.right_window.refresh()
        self.path_indicator.refresh()
        self.last_action_description.refresh()
        self.hotkey_guide.refresh()

        curses.doupdate()

    def clear_panes(self):
        self.left_window.clear()
        self.main_window.clear()
        self.right_window.clear()
        self.path_indicator.clear()
        self.last_action_description.clear()
        self.hotkey_guide.clear()

    def render_input_textbox(self, y_position, placeholder=FsItem("")):
        edit_box_width = self.pane_width - 2
        edit_window = curses.newwin(1, edit_box_width, y_position + 1, self.pane_width + 1)
        text_attribute = self.main_window.calculate_attributes(placeholder)
        self.main_window.get_window().addnstr(y_position, 0, ">", 1, text_attribute)
        self.main_window.refresh()

        original_name_text = utility.fit_text_to_line_length(edit_box_width, placeholder.get_clean_name())
        edit_window.addstr(0, 0, original_name_text)
        box = Textbox(edit_window)

        box.edit()

        message = box.gather()
        return str(message.strip("',/\n "))

    def render_create_folder_input_textbox(self, num_main_lines):
        y_position = self.main_window.calculate_max_line_to_render(num_main_lines - 1) + 1
        new_folder_name = self.render_input_textbox(y_position)
        return new_folder_name

    def render_rename_input_textbox(self, main_selected_line_i, currently_selected_item):
        y_to_render_at = main_selected_line_i - self.main_window.lines_render_offset
        new_name = self.render_input_textbox(y_to_render_at, currently_selected_item)
        return new_name
