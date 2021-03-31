import subprocess
import logging


def get_ls(directory="."):
    logging.debug('will check ls for: {}'.format(directory))
    cwd_ls = ""
    try:
        cwd_ls = subprocess.check_output(
            ["ls", directory, "-a", "--w=1", "-F", "--group-directories-first"])
    except subprocess.CalledProcessError as result_error:
        logging.warning('error when trying to ls a folder: {}'.format(result_error))
        return []

    all_lines = list(map(lambda s: s.decode("utf-8"), cwd_ls.splitlines()))
    lines = all_lines[2:]  # drop first 2 lines which are not folders
    logging.debug('ls {} output: {} items'.format(directory, len(lines)))

    # drop symbolic links, sockets, named pipes and doors
    lines = list(filter(lambda l: not l.endswith("@") and\
          not l.endswith("=") and\
          not l.endswith("|") and\
          not l.endswith(">"), lines))
    return lines


def open():
    # try different terminals until one of them works
    terminal_commands = [
        ["exo-open", "--working-directory", "/Repos", "--launch", "TerminalEmulator"],
        ["x-terminal-emulator"],
        ["urxvt"]
    ]
    for command_array in terminal_commands:
        try:
            subprocess.call(command_array)
            break
        except OSError:
            logging.warning("terminal not found: {}".format(command_array))
