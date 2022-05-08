"""
    Executes terminal commands and for some returns their output.
"""

import subprocess
import logging
from fs_item import FsItem

from pathlib import Path
import utility


def provide_initial_cwd():
    home_path = str(Path.home()) + "/"
    logging.info("initial cwd: {}", home_path)
    return home_path


def get_ls(directory="."):
    logging.debug('will check ls for: {}'.format(directory))
    try:
        cwd_ls = subprocess.check_output(
            ["ls", directory, "-a", "--w=1", "-F", "--group-directories-first"])
    except subprocess.CalledProcessError as result_error:
        logging.warning('error when trying to ls a folder: {}'.format(result_error))
        return []

    all_lines = list(map(lambda s: s.decode("utf-8"), cwd_ls.splitlines()))
    useful_lines = all_lines[2:]  # drop first 2 lines which are not folders
    fixed_lines = list(map(lambda l: l[:-1] if l.endswith("*") else l, useful_lines))
    logging.debug('ls {} output: {} items'.format(directory, len(fixed_lines)))

    # drop symbolic links, sockets, named pipes and doors
    lines = list(filter(lambda l: not l.endswith("@") and
                        not l.endswith("=") and
                        not l.endswith("|") and
                        not l.endswith(">"), fixed_lines))

    return list(map(lambda vl: FsItem(vl), lines))


def open_new_terminal(directory_to_open_in):
    # try different terminals until one of them works
    terminal_commands = [
        ["exo-open", "--working-directory", directory_to_open_in, "--launch", "TerminalEmulator"],
        ["x-terminal-emulator"],
        ["urxvt"]
    ]
    execute_one_of_multiple_terminal_calls(terminal_commands)


def open_file(full_path):
    if utility.is_folder(full_path):
        return

    # try different terminals until one of them works
    terminal_commands = [
        ['xdg-open', full_path],
        ['open', full_path],
    ]
    for command_array in terminal_commands:
        try:
            subprocess.Popen(command_array, close_fds=True)
            break  # stop trying others on success
        except OSError:
            logging.warning("could not execute open file command: {}".format(command_array))


def get_users_trash_path():
    home_of_logged_in_user = str(Path.home())
    return home_of_logged_in_user + "/.local/share/Trash/files/"


def delete(path_to_delete):
    delete_commands = [
        ["gio", "trash", path_to_delete],
        ["mv", path_to_delete, "trash://"],
        ["mv", path_to_delete, get_users_trash_path()]
    ]
    execute_one_of_multiple_terminal_calls(delete_commands)
    return path_to_delete


def permanent_delete(path_to_delete):
    terminal_command = ["rm", path_to_delete]
    if utility.is_folder(path_to_delete):
        terminal_command.insert(1, "-r")
    execute_terminal_call(terminal_command)


def make_new_folder(path_of_folder_to_make):
    if utility.is_folder(path_of_folder_to_make):
        path_of_folder_to_make = path_of_folder_to_make[:-1]
    terminal_command = ["mkdir", path_of_folder_to_make]
    execute_terminal_call(terminal_command)


def move(old_path, new_path):
    terminal_command = ["mv", old_path, new_path]
    execute_terminal_call(terminal_command)


def copy_paste(old_path, new_path):
    terminal_command = ["cp", old_path, new_path]
    if utility.is_folder(old_path):
        terminal_command.insert(1, "-r")

    execute_terminal_call(terminal_command)


def execute_terminal_call(terminal_command):
    try:
        subprocess.call(terminal_command)
    except OSError:
        logging.error("could not execute terminal call: {}".format(terminal_command))


def execute_one_of_multiple_terminal_calls(commands):
    for command_array in commands:
        try:
            subprocess.call(command_array)
            break  # stop trying others on success
        except OSError:
            logging.warning("terminal call not supported: {}".format(command_array))
