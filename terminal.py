"""
    Executes terminal commands and for some returns their output.
"""
import shutil
import subprocess
import logging
from pathlib import Path
import os
from send2trash import send2trash

from fs_item import FsItem
import utility


def provide_initial_cwd():
    home_path = os.getenv("HOME") + "/"
    logging.info("initial cwd: {}".format(home_path))
    return home_path


def list_all_in(directory="."):
    logging.debug('will check ls for: {}'.format(directory))

    files = []
    directories = []
    with os.scandir() as found_fs_items:
        for entry in found_fs_items:
            if entry.is_file():
                files.append(entry.name)
            if entry.is_dir():
                directories.append(entry.name + "/")

    all_fs_items = directories + files

    all_lines = list(map(lambda s: s.decode("utf-8"), all_fs_items))
    fixed_lines = list(map(lambda l: l[:-1] if l.endswith("*") else l, all_lines))
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
    for command in terminal_commands:
        try:
            subprocess.call(command)
            break  # stop trying others on success
        except OSError:
            logging.warning("terminal call not supported: {}".format(command))


def open_file(full_path):
    if utility.is_folder(full_path):
        return

    # try different terminals until one of them works
    terminal_commands = [
        ['xdg-open', full_path],
        ['open', full_path],
    ]
    for command in terminal_commands:
        try:
            subprocess.Popen(command, close_fds=True)
            break  # stop trying others on success
        except OSError:
            logging.warning("could not execute open file command: {}".format(command))


def get_users_trash_path():
    home_of_logged_in_user = str(Path.home())
    return home_of_logged_in_user + "/.local/share/Trash/files/"


def delete(path_to_delete):
    send2trash(path_to_delete)
    return path_to_delete


def permanent_delete(path_to_delete):
    shutil.rmtree(path_to_delete, ignore_errors=True)


def make_new_folder(path_of_folder_to_make):
    if utility.is_folder(path_of_folder_to_make):
        path_of_folder_to_make = path_of_folder_to_make.rstrip('/')
    if os.path.exists(path_of_folder_to_make):
        return False
    else:
        os.makedirs(path_of_folder_to_make)
        return True


def move(old_path, new_path):
    shutil.move(old_path, new_path)


def copy_paste(old_path, new_path):
    shutil.copy2(old_path, new_path)
