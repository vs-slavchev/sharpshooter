"""
    Interacts with the file system, executes terminal commands and for some returns their output.
"""
import shutil
import subprocess
import logging
import os
from datetime import datetime

import platform_utils
from fs_item import FsItem
import utility
from file_system_error import FileSystemError


def provide_initial_cwd():
    home_path = os.path.expanduser('~') + '/'
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
    for cmd in platform_utils.terminal_candidates(directory_to_open_in):
        try:
            # cwd= ensures xterm (which has no working-dir flag) opens in the right place;
            # it is harmless for terminals that use explicit flags.
            subprocess.call(cmd, cwd=directory_to_open_in)
            return
        except OSError:
            logging.warning("terminal call not supported: {}".format(cmd))


def open_file(full_path):
    if utility.is_folder(full_path):
        return
    if platform_utils.platform_type() == 'macos':
        cmd = ['open', full_path]
    else:
        cmd = ['xdg-open', full_path]
    try:
        subprocess.Popen(cmd, close_fds=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        logging.warning("could not execute open file command: {}".format(cmd))


# ---------------------------------------------------------------------------
# Trash helpers
# ---------------------------------------------------------------------------

def get_users_trash_path():
    if platform_utils.platform_type() == 'macos':
        return os.path.expanduser('~/.Trash/')
    return os.path.expanduser('~/.local/share/Trash/files/')


def _trash_info_dir():
    return os.path.expanduser('~/.local/share/Trash/info/')


def _write_trashinfo(trashed_name, original_path):
    """Write a freedesktop .trashinfo metadata file (Linux only)."""
    info_path = _trash_info_dir() + trashed_name + '.trashinfo'
    deletion_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    content = '[Trash Info]\nPath={}\nDeletionDate={}\n'.format(
        original_path, deletion_date)
    try:
        os.makedirs(_trash_info_dir(), exist_ok=True)
        with open(info_path, 'w') as f:
            f.write(content)
    except OSError:
        pass  # non-fatal: the file is in the trash, metadata is just missing


def _remove_trashinfo(trashed_name):
    """Remove the .trashinfo metadata file when a file is restored (Linux only)."""
    info_path = _trash_info_dir() + trashed_name + '.trashinfo'
    try:
        os.remove(info_path)
    except OSError:
        pass


def delete(path_to_delete):
    trash_path = get_users_trash_path()
    os.makedirs(trash_path, exist_ok=True)

    # Strip trailing slash for name extraction; keep original for the actual move.
    original_path = path_to_delete.rstrip('/')
    trashed_name = os.path.basename(original_path)

    try:
        move(path_to_delete, trash_path)
        if platform_utils.platform_type() == 'linux':
            _write_trashinfo(trashed_name, original_path)
        return path_to_delete
    except shutil.Error:  # name collision in trash
        timestamp_string = datetime.now().strftime("_%d-%m-%Y_%H-%M-%S")
        trashed_name = trashed_name + timestamp_string
        move(path_to_delete, trash_path + trashed_name)
        if platform_utils.platform_type() == 'linux':
            _write_trashinfo(trashed_name, original_path)
        return original_path + timestamp_string


def restore_from_trash(file_name, original_path):
    """Move a file back from the platform trash to its original location."""
    path_in_trash = get_users_trash_path() + file_name
    move(path_in_trash, original_path)
    if platform_utils.platform_type() == 'linux':
        _remove_trashinfo(file_name)


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
