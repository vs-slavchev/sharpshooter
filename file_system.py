"""
    Interacts with the file system, executes terminal commands and for some returns their output.
"""
import shutil
import subprocess
import logging
import os
from datetime import datetime

from fs_item import FsItem
import utility
from file_system_error import FileSystemError


def provide_initial_cwd():
    home_path = os.getenv("HOME") + "/"
    logging.info("initial cwd: {}".format(home_path))
    return home_path


def list_all_in(directory):
    logging.debug('listing files/dirs in: {}'.format(directory))

    files = []
    directories = []
    try:
        with os.scandir(directory) as found_fs_items:
            for entry in found_fs_items:
                if entry.is_file():
                    files.append(entry.name)
                elif entry.is_dir():
                    directories.append(entry.name + "/")
    except (PermissionError, OSError):
        # ignore not having permissions to list a dir
        pass

    all_fs_items = sorted(directories) + sorted(files)
    cleaned_lines = list(map(lambda l: l[:-1] if l.endswith("*") else l, all_fs_items))

    # drop symbolic links, sockets, named pipes and doors
    lines = list(filter(lambda l: not l.endswith("@") and
                        not l.endswith("=") and
                        not l.endswith("|") and
                        not l.endswith(">"), cleaned_lines))
    logging.debug('scandir {} output: {} items'.format(directory, len(lines)))

    return list(map(lambda vl: FsItem(vl), lines))


def open_new_terminal(directory_to_open_in):
    logging.info("opening terminal in: {}".format(directory_to_open_in))

    # try different terminals until one of them works
    terminal_commands = [
        ["exo-open", "--working-directory", directory_to_open_in, "--launch", "TerminalEmulator"],
        ["x-terminal-emulator", "--working-directory", directory_to_open_in],
        ["gnome-terminal", "--working-directory", directory_to_open_in],
        ["xfce4-terminal", "--working-directory", directory_to_open_in],
        ["konsole", "--workdir", directory_to_open_in],
        ["urxvt", "-cd", directory_to_open_in]
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

    # try different commands until one of them works
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
    home_of_logged_in_user = os.getenv("HOME")
    return home_of_logged_in_user + "/.local/share/Trash/files/"


def delete(path_to_delete):
    try:
        move(path_to_delete, get_users_trash_path())
        return path_to_delete
    except shutil.Error:  # file with this name already exists
        if utility.is_folder(path_to_delete):
            path_to_delete = path_to_delete[:-1]
        fs_item_name = utility.extract_item_name_from_path(path_to_delete)
        timestamp_string = datetime.now().strftime("_%d-%m-%Y_%H-%M-%S")
        move(path_to_delete, get_users_trash_path() + fs_item_name + timestamp_string)
        return path_to_delete + timestamp_string


def permanent_delete(path_to_delete):
    shutil.rmtree(path_to_delete, ignore_errors=True)


def make_new_folder(path_of_folder_to_make):
    if utility.is_folder(path_of_folder_to_make):
        path_of_folder_to_make = path_of_folder_to_make.rstrip('/')
    if os.path.exists(path_of_folder_to_make):
        raise FileSystemError("Already exists")
    else:
        try:
            os.makedirs(path_of_folder_to_make)
        except (PermissionError, OSError):
            raise FileSystemError("No permissions to make a folder here")


def move(old_path, new_path):
    try:
        shutil.move(old_path, new_path)
    except (PermissionError, shutil.Error, OSError):
        raise FileSystemError("No permission to move")


def copy_paste(old_path, new_path):
    logging.info("pasting from {} to {}".format(old_path, new_path))
    try:
        if utility.is_folder(old_path):
            old_path_no_slash = old_path[:-1]
            folder_name = utility.extract_item_name_from_path(old_path)
            new_folder_path = new_path + folder_name[:-1]
            while os.path.exists(new_folder_path):
                new_folder_path = new_folder_path + "_copy"

            shutil.copytree(old_path_no_slash, new_folder_path, dirs_exist_ok=True)
        else:
            file_name = utility.extract_item_name_from_path(old_path)
            new_path = new_path + file_name
            while os.path.exists(new_path):
                new_path = new_path + "_copy"
            shutil.copy2(old_path, new_path)
    except (PermissionError, shutil.Error, OSError):
        raise FileSystemError("No permission to paste")
