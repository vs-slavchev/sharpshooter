import subprocess
import logging

def get_ls():
    cwd_ls = subprocess.check_output(
        ["ls", "-a", "--w=1", "-F", "--group-directories-first"])
    logging.debug('ls output: {}'.format(cwd_ls))
    all_lines = cwd_ls.split()
    lines = all_lines[2:]
    return lines

def open():
    # try different terminals until one of them works
    terminal_commands = [["x-terminal-emulator"], ["urxvt"]]
    for command_array in terminal_commands:
        try:
            subprocess.call(command_array)
            break
        except OSError:
            logging.warning("terminal not found: {}".format(command_array))
