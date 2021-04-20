import subprocess
import logging

from pathlib import Path


def get_ls(directory="."):
    logging.debug('will check ls for: {}'.format(directory))
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


def open_new_terminal(directory_to_open_in):
    # try different terminals until one of them works
    terminal_commands = [
        ["exo-open", "--working-directory", directory_to_open_in, "--launch", "TerminalEmulator"],
        ["x-terminal-emulator"],
        ["urxvt"]
    ]
    for command_array in terminal_commands:
        try:
            subprocess.call(command_array)
            break  # stop trying others on success
        except OSError:
            logging.warning("terminal not found: {}".format(command_array))


def open_file(full_path):
    is_folder = full_path.endswith("/")
    if is_folder:
        return

    # try different terminals until one of them works
    terminal_commands = [
        ['gnome-terminal', '--execute', 'rifle', full_path],
        ['xterm', '-e', 'rifle', full_path],
        ['rxvt', '-e', 'rifle', full_path],
    ]
    for command_array in terminal_commands:
        try:
            subprocess.Popen(command_array, close_fds=True)
            break  # stop trying others on success
        except OSError:
            logging.warning("could not execute open file command: {}".format(command_array))


def delete(path_to_delete):
    home_of_logged_in_user = str(Path.home())
    terminal_command = ["mv", path_to_delete, home_of_logged_in_user + "/.local/share/Trash/files/"]
    try:
        subprocess.call(terminal_command)
    except OSError:
        logging.warning("could not execute delete: {}".format(command_array))


def make_new_folder(path_of_folder_to_make):
    terminal_command = ["mkdir", path_of_folder_to_make]
    try:
        subprocess.call(terminal_command)
    except OSError:
        logging.warning("could not execute making new folder: {}".format(command_array))


def rename(old_path, new_path):
    terminal_command = ["mv", old_path, new_path]
    try:
        subprocess.call(terminal_command)
    except OSError:
        logging.warning("could not execute rename: {}".format(command_array))
