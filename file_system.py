"""
    Interacts with the file system, executes terminal commands and for some returns their output.
"""
import base64
import shutil
import subprocess
import logging
import os
import sys
import threading
import urllib.parse
import zipfile
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


# ---------------------------------------------------------------------------
# Launching external programs
# ---------------------------------------------------------------------------

# How long to wait for a launched program to report failure. Launchers like xdg-open or gnome-terminal
# exit quickly with a status; programs that keep running past this are assumed to have started fine.
_LAUNCH_GRACE_SECONDS = 0.5
# How long a tool that is expected to finish (e.g. a clipboard copier) may take before it counts as hung.
_FINISH_TIMEOUT_SECONDS = 1


def run_first_working(candidates, cwd=None, stdin_text=None, must_finish=False):
    """Try each argv list in order until one starts successfully.
    Output is discarded so it never draws over the curses UI, and programs run detached in their own session.
    A program still running after the grace period counts as started, unless must_finish is set (for short
    tools like clipboard copiers): then it has to exit successfully within _FINISH_TIMEOUT_SECONDS, or it is stopped.
    Returns the argv that worked, or None if none did."""
    timeout = _FINISH_TIMEOUT_SECONDS if must_finish else _LAUNCH_GRACE_SECONDS
    stdin = subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL
    for cmd in candidates:
        if not cmd or shutil.which(cmd[0]) is None:
            continue
        stdin_bytes = _encode_for(cmd, stdin_text) if stdin_text is not None else None
        try:
            proc = subprocess.Popen(cmd, cwd=cwd, stdin=stdin,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    start_new_session=True)
        except OSError as e:
            logging.warning("could not start {}: {}".format(cmd, e))
            continue
        try:
            proc.communicate(stdin_bytes, timeout=timeout)
            return_code = proc.returncode
        except subprocess.TimeoutExpired:
            if must_finish:
                logging.warning("{} hung, stopping it".format(cmd))
                proc.kill()
                threading.Thread(target=proc.wait, daemon=True).start()
                continue
            logging.info("started (still running): {}".format(cmd))
            # reap it when it eventually exits so it does not linger as a zombie
            threading.Thread(target=proc.wait, daemon=True).start()
            return cmd
        except OSError as e:
            logging.warning("{} failed: {}".format(cmd, e))
            continue
        if return_code == 0:
            logging.info("ran: {}".format(cmd))
            return cmd
        logging.warning("{} exited with {}".format(cmd, return_code))
    return None


def _encode_for(cmd, text):
    encoding = platform_utils.stdin_encoding(cmd)
    if encoding == 'utf-8':
        return os.fsencode(text)  # the name's real bytes, even if not valid UTF-8
    return text.encode(encoding, errors='replace')


def open_new_terminal(directory_to_open_in):
    logging.info("opening terminal in: {}".format(directory_to_open_in))
    candidates = platform_utils.terminal_candidates(directory_to_open_in)
    if run_first_working(candidates, cwd=directory_to_open_in) is None:
        raise FileSystemError("No terminal could be opened. Set $TERMINAL or install one, e.g. xterm")


def open_file(full_path):
    if utility.is_folder(full_path):
        return
    candidates = platform_utils.open_file_candidates(full_path)
    if run_first_working(candidates, cwd=os.path.dirname(full_path) or None) is None:
        raise FileSystemError("No application could open [{}]. {}".format(
            os.path.basename(full_path), platform_utils.open_file_install_hint()))


def copy_with_clipboard_tools(text):
    """Copy text with the first clipboard tool that works. Returns True if one confirmed the copy.
    Safe to call from a background thread: nothing is written to the terminal."""
    return run_first_working(platform_utils.clipboard_candidates(), stdin_text=text, must_finish=True) is not None


def copy_via_osc52(text):
    """Ask the terminal emulator itself to set the clipboard. Works in many terminals and over SSH.
    Writes to the terminal, so call it only from the main thread, between screen updates."""
    payload = base64.b64encode(os.fsencode(text)).decode()  # the name's real bytes, even if not valid UTF-8
    sequence = "\033]52;c;{}\a".format(payload)
    if os.getenv('TMUX'):
        sequence = "\033Ptmux;{}\033\\".format(sequence.replace("\033", "\033\033"))
    try:
        sys.stdout.write(sequence)
        sys.stdout.flush()
    except (OSError, ValueError) as e:
        logging.warning("OSC 52 failed: {}".format(e))
        raise FileSystemError("No clipboard tool worked and the terminal could not be reached. "
                              + platform_utils.clipboard_install_hint())


# ---------------------------------------------------------------------------
# Trash helpers
# ---------------------------------------------------------------------------

def get_users_trash_path():
    if platform_utils.platform_type() == 'macos':
        return os.path.expanduser('~/.Trash/')
    return os.path.expanduser('~/.local/share/Trash/files/')


def _uses_freedesktop_trash():
    return platform_utils.platform_type() == 'linux'


def _trash_info_dir():
    return os.path.expanduser('~/.local/share/Trash/info/')


def _write_trashinfo(trashed_name, original_path):
    """Create a freedesktop .trashinfo metadata file; raises FileExistsError if the name is already claimed."""
    deletion_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    # the freedesktop spec stores the path percent-encoded, like a URI path
    content = '[Trash Info]\nPath={}\nDeletionDate={}\n'.format(
        urllib.parse.quote(os.fsencode(original_path)), deletion_date)
    os.makedirs(_trash_info_dir(), exist_ok=True)
    with open(_trash_info_dir() + trashed_name + '.trashinfo', 'x') as f:
        f.write(content)


def _trashinfo_original_path(trashed_name):
    """The original path recorded for a trashed item, or None if there is no readable metadata."""
    try:
        with open(_trash_info_dir() + trashed_name + '.trashinfo') as f:
            for line in f:
                if line.startswith('Path='):
                    return os.fsdecode(urllib.parse.unquote_to_bytes(line[len('Path='):].strip()))
    except OSError:
        pass
    return None


def _remove_trashinfo(trashed_name):
    """Remove the .trashinfo metadata file when a file is restored (Linux only)."""
    remove_file(_trash_info_dir() + trashed_name + '.trashinfo')


def delete(path_to_delete):
    """Move an item to the platform trash.
    Returns (trashed_name, original_path) for undo, or None if the item was trashed in a way
    Sharpshooter cannot undo (via Finder on macOS)."""
    original_path = path_to_delete.rstrip('/')
    trash_path = get_users_trash_path()
    try:
        os.makedirs(trash_path, exist_ok=True)
        trashed_name = _reserve_trash_name(os.path.basename(original_path), original_path)
        try:
            shutil.move(original_path, trash_path + trashed_name)
        except OSError as move_error:
            _clean_up_failed_trash_move(original_path, trashed_name, move_error)
            if os.path.lexists(trash_path + trashed_name):
                # a folder was copied into the trash but could not be fully removed from its place
                raise FileSystemError("Could not remove all of it ({}); a copy is in the trash".format(
                    _describe_os_error(move_error)))
            raise
    except OSError as e:
        logging.warning("moving {} to trash failed: {}".format(original_path, e))
        # macOS privacy protection blocks ~/.Trash itself unless the terminal has Full Disk Access.
        # Only then is Finder asked; any other problem is reported and the item stays where it is.
        # (it can surface as EPERM or EACCES; what tells it apart is that the Trash folder cannot be read)
        if not _uses_freedesktop_trash() and isinstance(e, PermissionError) and _trash_folder_unreadable() \
                and _delete_via_finder(original_path):
            return None
        raise FileSystemError(_describe_os_error(e))
    return trashed_name, original_path


def _clean_up_failed_trash_move(original_path, trashed_name, move_error):
    """After a failed move into the trash, leave no orphans. Moving across disks copies first, then removes
    the original. If the copy step failed (shutil.Error from copying a folder), or the original file is still
    there, the original is complete and the copy in the trash is dropped. If removing a folder's original
    failed partway, the trash copy is the only complete one: it and its metadata stay, restorable."""
    copy_in_trash = get_users_trash_path() + trashed_name
    if os.path.lexists(copy_in_trash):
        if isinstance(move_error, shutil.Error) and 'already exists' in str(move_error):
            return  # that item is someone else's, not a copy we made: never touch it
        copy_step_failed = isinstance(move_error, shutil.Error)
        original_is_complete = copy_step_failed or (os.path.isfile(original_path) and not os.path.isdir(copy_in_trash))
        if not original_is_complete:
            return  # keep the trash copy and its metadata, see above
        if os.path.isdir(copy_in_trash):
            permanent_delete(copy_in_trash)
        else:
            remove_file(copy_in_trash)
    if _uses_freedesktop_trash():
        _remove_trashinfo(trashed_name)  # release the reservation


def _reserve_trash_name(name, original_path):
    """Pick a free name in the trash. On freedesktop systems the name is claimed by creating its .trashinfo
    exclusively first, as the spec requires, so another program trashing the same name at the same time
    cannot take it."""
    while True:
        candidate = _unique_name(name, _taken_in_trash)
        if not _uses_freedesktop_trash():
            return candidate
        try:
            _write_trashinfo(candidate, original_path)
            return candidate
        except FileExistsError:
            continue  # someone claimed it just now: pick again
        except OSError as e:
            logging.warning("could not write trash metadata: {}".format(e))
            return candidate  # non-fatal: the item still goes to the trash, metadata is just missing


def _trash_folder_unreadable():
    try:
        os.listdir(get_users_trash_path())
        return False
    except PermissionError:
        return True


def unique_name_in(folder, name, extension=''):
    """name, or name with a timestamp (and a counter if needed) so that name + extension
    does not exist in folder. The extension itself is not part of the returned name."""
    return _unique_name(name, lambda candidate: os.path.lexists(folder + candidate + extension))


def claim_unique_name(folder, name, extension='', make_folder=False):
    """Like unique_name_in, but also creates the file (empty) or folder at once, exclusively, so nothing else
    can take or already own that path. Whatever is later written there, and cleaned up on failure, is ours."""
    while True:
        candidate = unique_name_in(folder, name, extension)
        path = folder + candidate + extension
        try:
            if make_folder:
                os.mkdir(path)
            else:
                open(path, 'x').close()
            return candidate
        except FileExistsError:
            continue  # taken just now: pick again
        except OSError as e:
            raise FileSystemError(_describe_os_error(e))


def _unique_name(name, is_taken):
    if not is_taken(name):
        return name
    stamped = name + '_' + utility.now()
    candidate = stamped
    counter = 1
    while is_taken(candidate):
        counter += 1
        candidate = '{}_{}'.format(stamped, counter)
    return candidate


def _taken_in_trash(name):
    if os.path.lexists(get_users_trash_path() + name):
        return True
    # an orphaned .trashinfo still describes some other item: do not overwrite it
    return _uses_freedesktop_trash() and os.path.lexists(_trash_info_dir() + name + '.trashinfo')


def is_in_trash(trashed_name, original_path=None):
    """True if the item is still in the trash. With original_path, also check that the item under that name
    really is the one deleted from there, not another item that took the same name later."""
    if not os.path.lexists(get_users_trash_path() + trashed_name):
        return False
    if original_path is None or not _uses_freedesktop_trash():
        return True
    recorded = _trashinfo_original_path(trashed_name)
    return recorded is None or recorded == original_path


def _delete_via_finder(path):
    escaped = path.replace('\\', '\\\\').replace('"', '\\"')
    script = 'tell application "Finder" to delete (POSIX file "{}")'.format(escaped)
    try:
        result = subprocess.run(['osascript', '-e', script], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as e:
        logging.warning("Finder delete failed: {}".format(e))
        return False


def restore_from_trash(trashed_name, original_path):
    """Move a file back from the platform trash to its original location."""
    if os.path.lexists(original_path):
        raise FileSystemError("Something already exists at the original location")
    if not is_in_trash(trashed_name, original_path):
        raise FileSystemError("It is no longer in the trash")
    if not os.path.isdir(os.path.dirname(original_path)):
        raise FileSystemError("Its original folder no longer exists")
    path_in_trash = get_users_trash_path() + trashed_name
    move(path_in_trash, original_path)
    if _uses_freedesktop_trash():
        _remove_trashinfo(trashed_name)


def remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


def permanent_delete(path_to_delete):
    shutil.rmtree(path_to_delete, ignore_errors=True)


def zip_items(paths, archive_path, contents_only=False):
    """Write files and folders into one zip archive, each at the archive root under its own name.
    With contents_only, a single folder's contents go at the root instead (unzipping then recreates the folder).
    Only regular files are stored: broken links, pipes and sockets are skipped, so a pipe can never hang the zip."""
    # strict_timestamps=False: files dated before 1980 (zip's earliest date) are stored as 1980, not refused
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, strict_timestamps=False) as archive:
        for path in paths:
            path = path.rstrip('/')
            name = os.path.basename(path)
            if os.path.islink(path) and os.path.isdir(path):
                raise FileSystemError("Cannot zip [{}]: links to folders are not followed".format(name))
            if os.path.isdir(path):
                _zip_tree(archive, path, '' if contents_only else name)
            elif os.path.isfile(path):
                _write_if_regular_file(archive, path, name)
            else:
                raise FileSystemError("Cannot zip [{}]: not a regular file or folder".format(name))


def _zip_tree(archive, root, arc_root):
    """Store a folder tree. Links to folders are not followed (a link to / or .. would pull in huge trees).
    Anything that cannot be read fails the whole zip, rather than leaving a silently incomplete archive."""
    def unreadable(error):
        raise FileSystemError("Cannot read [{}]".format(error.filename))

    for folder, _subfolders, files in os.walk(root, onerror=unreadable):
        rel = os.path.relpath(folder, root)
        arc_folder = os.path.normpath(os.path.join(arc_root, rel)) if rel != '.' else arc_root
        if arc_folder:
            archive.write(folder, arc_folder)
        for name in files:
            _write_if_regular_file(archive, os.path.join(folder, name), os.path.join(arc_folder, name))


def _write_if_regular_file(archive, file_path, arc_name):
    if not os.path.isfile(file_path):
        logging.warning("skipping in zip (not a regular file): {}".format(file_path))
        return
    try:
        archive.write(file_path, arc_name)
    except PermissionError:
        raise FileSystemError("Cannot read [{}]".format(file_path))


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


def rename(old_path, new_path):
    """Rename in place. Unlike move, never moves the item into a folder that happens to have the new name."""
    old, new = old_path.rstrip('/'), new_path.rstrip('/')
    if old == new:
        return  # name unchanged: nothing to do
    if os.path.lexists(new) and not _is_case_only_rename(old, new):
        raise FileSystemError("Destination already exists")
    move(old_path, new_path)


def _is_case_only_rename(old, new):
    """On case-insensitive file systems (the macOS default) 'readme' and 'README' are the same entry.
    Compares the entries themselves (lstat), so a link pointing at the item does not count as the item."""
    if old.lower() != new.lower():
        return False
    try:
        old_stat, new_stat = os.lstat(old), os.lstat(new)
    except OSError:
        return False
    return (old_stat.st_dev, old_stat.st_ino) == (new_stat.st_dev, new_stat.st_ino)


def move(old_path, new_path):
    try:
        shutil.move(old_path, new_path)
    except OSError as e:  # includes PermissionError and shutil.Error
        raise FileSystemError(_describe_os_error(e)) from e


def _describe_os_error(error):
    if isinstance(error, PermissionError):
        return "No permission"
    if isinstance(error, shutil.Error):
        text = str(error)
        if 'already exists' in text:
            return "Destination already exists"
        if 'into itself' in text:
            return "Cannot move a folder into itself"
        return "Some files could not be copied"
    return error.strerror or "Could not complete the operation"


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
    except OSError as e:  # includes PermissionError and shutil.Error
        raise FileSystemError(_describe_os_error(e))
