import curses
import logging
import subprocess

import cursed_window

logging.basicConfig(filename='last_run.log',level=logging.DEBUG,filemode='w')

def main(standard_screen):
    curses.curs_set(False)
    standard_screen.clear()

    logging.debug("started")

    cwd_ls = subprocess.check_output(
        ["ls", "-a", "--w=1", "-F", "--group-directories-first"])
    logging.debug('ls output: {}'.format(cwd_ls))
    all_lines = cwd_ls.split()
    lines = all_lines[2:]

    main_window = cursed_window.CursedWindow(2, 1, 25, 20)
    main_window.set_text_content(lines)
    main_window.render()

    standard_screen.refresh()
    main_window.refresh()
    standard_screen.getkey()

curses.wrapper(main)
