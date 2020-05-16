import subprocess

def open():
    # try different terminals until one of them works
    terminal_commands = [["x-terminal-emulator"], ["urxvt"]]
    for command_array in terminal_commands:
        try:
            subprocess.call(command_array)
            break
        except OSError:
            logging.warning("terminal not found: {}".format(command_array))
