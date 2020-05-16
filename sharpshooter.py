import curses

def main(standard_screen):
    curses.curs_set(False)
    standard_screen.clear()

    standard_screen.addstr("mandatory curse word to test")

    standard_screen.refresh()
    standard_screen.getkey()

curses.wrapper(main)
