import subprocess
import logging


def get_ls(directory="."):
    cwd_ls = subprocess.check_output(
        ["ls", directory, "-a", "--w=1", "-F", "--group-directories-first"])
    all_lines = cwd_ls.split()
    lines = all_lines[2:] # drop first 2 lines which are not folders
    logging.debug('ls output: {} items'.format(len(lines)))
    return lines


def open():
    # try different terminals until one of them works
    terminal_commands = [
            ["exo-open","--working-directory","/Repos","--launch","TerminalEmulator"],
            ["x-terminal-emulator"],
            ["urxvt"]
        ]
    for command_array in terminal_commands:
        try:
            subprocess.call(command_array)
            break
        except OSError:
            logging.warning("terminal not found: {}".format(command_array))
