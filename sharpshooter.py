import curses
import logging

from cursed_window import CursedWindow
import terminal

logging.basicConfig(filename='last_run.log',level=logging.DEBUG,filemode='w')

def main(standard_screen):
    curses.curs_set(False)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    # keys
    down_key = "n"

    logging.info("sharpshooter started")
    logging.info("curses version: {}".format(str(curses.version.decode())))

    screen_height, screen_width = standard_screen.getmaxyx()
    logging.debug("screen size WxH: {}".format(screen_width, screen_height))
    window_width = screen_width // 3
    window_y = 1
    window_height = screen_height - window_y

    left_window = CursedWindow(1, window_y, window_width -1, window_height)
    main_window = CursedWindow(window_width, window_y, window_width, window_height)
    right_window = CursedWindow(window_width*2, window_y, window_width, window_height)
    selected_line_i = 0

    is_working = True
    while is_working:
        standard_screen.clear()

        left_window.set_text_content(terminal.get_ls(".."))
        left_window.render()

        cwd_lines = terminal.get_ls()
        main_window.set_text_content(cwd_lines)
        main_window.render()

        right_window.set_text_content(terminal.get_ls(cwd_lines[selected_line_i]))
        right_window.render()

        standard_screen.refresh()
        left_window.refresh()
        main_window.refresh()
        right_window.refresh()

        input_key = standard_screen.getkey()
        logging.info("input: {}".format(input_key))
        if input_key == down_key:
            selected_line_i = selected_line_i + 1
            main_window.set_selected_line_i(selected_line_i)
        #terminal.open()

curses.wrapper(main)
