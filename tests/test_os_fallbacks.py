import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import file_system
import platform_utils
from content import Content
from file_system_error import FileSystemError
from fs_item import FsItem
from tests.helpers import SyncThread

cwd = '/a/aa/aac/'
mock_directory_contents = {cwd: ['aaaa', 'aaab.zip'], '/a/aa/': ['aac/']}


def mock_return_values(arg):
    return list(map(lambda vl: FsItem(vl), mock_directory_contents[arg]))


def make_proc(return_code=0, still_running=False):
    proc = mock.Mock()
    proc.returncode = return_code
    if still_running:
        proc.communicate.side_effect = subprocess.TimeoutExpired('cmd', 0.5)
    return proc


def which_only(*installed):
    return lambda exe: '/usr/bin/' + exe if exe in installed else None


class TestRunFirstWorking(unittest.TestCase):

    @mock.patch('file_system.subprocess.Popen')
    @mock.patch('file_system.shutil.which', side_effect=which_only('b'))
    def test_skips_programs_that_are_not_installed(self, _which, popen):
        popen.return_value = make_proc(0)
        self.assertEqual(['b'], file_system.run_first_working([['a'], ['b']]))
        popen.assert_called_once()

    @mock.patch('file_system.subprocess.Popen')
    @mock.patch('file_system.shutil.which', side_effect=which_only('a', 'b'))
    def test_falls_back_when_a_program_exits_with_an_error(self, _which, popen):
        popen.side_effect = [make_proc(1), make_proc(0)]
        self.assertEqual(['b'], file_system.run_first_working([['a'], ['b']]))

    @mock.patch('file_system.subprocess.Popen')
    @mock.patch('file_system.shutil.which', side_effect=which_only('a', 'b'))
    def test_a_program_still_running_counts_as_started(self, _which, popen):
        popen.return_value = make_proc(still_running=True)
        self.assertEqual(['a'], file_system.run_first_working([['a'], ['b']]))

    @mock.patch('file_system.subprocess.Popen')
    @mock.patch('file_system.shutil.which', side_effect=which_only('a', 'b'))
    def test_a_hung_tool_that_must_finish_is_stopped_and_skipped(self, _which, popen):
        hung = make_proc(still_running=True)
        popen.side_effect = [hung, make_proc(0)]
        self.assertEqual(['b'], file_system.run_first_working([['a'], ['b']], must_finish=True))
        hung.kill.assert_called_once()

    @mock.patch('file_system.subprocess.Popen')
    @mock.patch('file_system.shutil.which', side_effect=which_only('clip.exe'))
    def test_clip_exe_gets_utf16(self, _which, popen):
        proc = make_proc(0)
        popen.return_value = proc
        file_system.run_first_working([['clip.exe']], stdin_text='résumé')
        self.assertEqual('résumé'.encode('utf-16'), proc.communicate.call_args[0][0])

    @mock.patch('file_system.shutil.which', return_value=None)
    def test_returns_none_when_nothing_works(self, _which):
        self.assertIsNone(file_system.run_first_working([['a'], ['b']]))


class TestCandidates(unittest.TestCase):

    @mock.patch('platform_utils.is_wsl', new=lambda: False)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_wayland_prefers_wl_copy(self, _platform):
        with mock.patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-0'}):
            self.assertEqual(['wl-copy'], platform_utils.clipboard_candidates()[0])

    @mock.patch('platform_utils.is_wsl', new=lambda: False)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_x11_prefers_xclip_and_still_offers_wl_copy(self, _platform):
        with mock.patch.dict(os.environ, {}, clear=True):
            candidates = platform_utils.clipboard_candidates()
        self.assertEqual('xclip', candidates[0][0])
        self.assertIn(['wl-copy'], candidates)

    @mock.patch('platform_utils.is_wsl', return_value=True)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_wsl_uses_windows_clipboard_first(self, _platform, _wsl):
        self.assertEqual(['clip.exe'], platform_utils.clipboard_candidates()[0])

    @mock.patch('platform_utils.is_wsl', new=lambda: False)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_terminal_env_var_is_tried_first(self, _platform):
        with mock.patch.dict(os.environ, {'TERMINAL': 'my-term --flag'}):
            self.assertEqual(['my-term', '--flag'], platform_utils.terminal_candidates('/x/')[0])

    @mock.patch('platform_utils.is_wsl', return_value=True)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_windows_terminal_gets_escaped_semicolons(self, _platform, _wsl):
        with mock.patch.dict(os.environ, {'WSL_DISTRO_NAME': 'Ubuntu'}, clear=True):
            first = platform_utils.terminal_candidates('/home/u/a;b/')[0]
        self.assertEqual(['wt.exe', 'wsl.exe', '-d', 'Ubuntu', '--cd', '/home/u/a\\;b/'], first)

    @mock.patch('platform_utils.is_wsl', new=lambda: False)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_system_default_terminal_comes_before_specific_ones_outside_their_desktop(self, _platform):
        with mock.patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'sway'}, clear=True):
            programs = [c[0] for c in platform_utils.terminal_candidates('/x/')]
        self.assertLess(programs.index('x-terminal-emulator'), programs.index('gnome-terminal'))

    @mock.patch('platform_utils.is_wsl', new=lambda: False)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_desktop_terminal_comes_first_on_its_desktop(self, _platform):
        with mock.patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE'}, clear=True):
            self.assertEqual('konsole', platform_utils.terminal_candidates('/x/')[0][0])

    @mock.patch('platform_utils.is_wsl', new=lambda: False)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_terminal_list_ends_with_xterm(self, _platform):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(['xterm'], platform_utils.terminal_candidates('/x/')[-1])

    @mock.patch('platform_utils.is_wsl', new=lambda: False)
    @mock.patch('platform_utils.platform_type', return_value='linux')
    def test_open_file_has_fallbacks_after_xdg_open(self, _platform):
        programs = [c[0] for c in platform_utils.open_file_candidates('/x/f.txt')]
        self.assertEqual('xdg-open', programs[0])
        self.assertIn('gio', programs)


class TestFailuresRaiseForTheUser(unittest.TestCase):

    @mock.patch('file_system.run_first_working', return_value=['xclip'])
    def test_clipboard_tool_confirms_copy(self, _run):
        self.assertTrue(file_system.copy_with_clipboard_tools('name'))

    @mock.patch('file_system.run_first_working', return_value=None)
    def test_no_clipboard_tool_is_reported(self, _run):
        self.assertFalse(file_system.copy_with_clipboard_tools('name'))

    @mock.patch('file_system.sys.stdout')
    def test_osc52_handles_names_that_are_not_valid_utf8(self, stdout):
        file_system.copy_via_osc52(os.fsdecode(b'caf\xe9'))
        self.assertIn('Y2Fm6Q==', stdout.write.call_args[0][0])  # base64 of the raw bytes

    @mock.patch('file_system.sys.stdout')
    def test_osc52_raises_when_the_terminal_cannot_be_written(self, stdout):
        stdout.write.side_effect = OSError
        with self.assertRaises(FileSystemError):
            file_system.copy_via_osc52('name')

    @mock.patch('file_system.run_first_working', return_value=None)
    def test_terminal_raises_when_nothing_works(self, _run):
        with self.assertRaises(FileSystemError):
            file_system.open_new_terminal('/x/')

    @mock.patch('file_system.run_first_working', return_value=None)
    def test_open_file_raises_when_nothing_works(self, _run):
        with self.assertRaises(FileSystemError):
            file_system.open_file('/x/f.txt')


class TestStatusLineReportsFailures(unittest.TestCase):

    def make_content(self, mock_fs):
        mock_fs.provide_initial_cwd.return_value = cwd
        mock_fs.list_all_in.side_effect = mock_return_values
        content = Content(mock.Mock())
        content.main_pane_selected_line_i = 0
        return content

    @mock.patch('content.threading.Thread', SyncThread)
    @mock.patch('content.file_system')
    def test_terminal_failure_is_shown_and_triggers_redraw(self, mock_fs):
        content = self.make_content(mock_fs)
        mock_fs.open_new_terminal.side_effect = FileSystemError("No terminal could be opened")
        content.open_new_terminal()
        self.assertEqual("No terminal could be opened.", content.last_action_description)
        self.assertTrue(content.background_changed.is_set())

    @mock.patch('content.threading.Thread', SyncThread)
    @mock.patch('content.file_system')
    def test_braces_in_error_messages_do_not_crash(self, mock_fs):
        content = self.make_content(mock_fs)
        mock_fs.open_file.side_effect = FileSystemError("No application could open [notes{1}.txt]")
        content.open_selected()
        self.assertEqual("No application could open [notes{1}.txt].", content.last_action_description)

    @mock.patch('content.file_system')
    def test_more_than_128_deletes_do_not_hang_and_keep_the_newest(self, mock_fs):
        content = self.make_content(mock_fs)
        for i in range(130):
            content.save_deletion_info(('f{}'.format(i), cwd + 'f{}'.format(i)))
        self.assertEqual(128, len(content.trash_undo_stack))
        self.assertEqual(('f129', cwd + 'f129'), content.trash_undo_stack[-1])

    @mock.patch('content.file_system')
    def test_failed_undo_can_be_retried_while_item_is_still_in_trash(self, mock_fs):
        content = self.make_content(mock_fs)
        content.save_deletion_info(('aaaa', cwd + 'aaaa'))
        mock_fs.restore_from_trash.side_effect = FileSystemError("Something already exists at the original location")
        mock_fs.is_in_trash.return_value = True
        content.undo()
        self.assertEqual(1, len(content.trash_undo_stack))

    @mock.patch('content.file_system')
    def test_failed_undo_does_not_block_older_deletes(self, mock_fs):
        content = self.make_content(mock_fs)
        content.save_deletion_info(('a', cwd + 'a'))
        content.save_deletion_info(('b', cwd + 'b'))
        mock_fs.restore_from_trash.side_effect = [FileSystemError("Something already exists"), None]
        mock_fs.is_in_trash.return_value = True
        content.undo()  # b fails and moves to the bottom
        content.undo()  # a is restored
        mock_fs.restore_from_trash.assert_called_with('a', cwd + 'a')
        self.assertEqual([('b', cwd + 'b')], list(content.trash_undo_stack))

    @mock.patch('content.file_system')
    def test_late_background_failure_keeps_the_newer_message(self, mock_fs):
        content = self.make_content(mock_fs)
        with mock.patch('content.threading.Thread') as thread:
            mock_fs.open_file.side_effect = FileSystemError("No application could open [aaaa]")
            content.open_selected()
            content.describe_last_action("Deleted [{}].", "aaab")  # user acts before the failure arrives
            thread.call_args.kwargs['target']()
        self.assertEqual("Deleted [aaab]. | No application could open [aaaa].", content.last_action_description)

    @mock.patch('content.threading.Thread')
    @mock.patch('content.file_system')
    def test_unzip_always_extracts_into_a_new_folder(self, mock_fs, _thread):
        content = self.make_content(mock_fs)
        content.main_pane_selected_line_i = 1  # aaab.zip
        mock_fs.claim_unique_name.return_value = 'aaab_17-11-2026-10-00-00'
        content.zip_unzip()
        mock_fs.claim_unique_name.assert_called_with(cwd, 'aaab', make_folder=True)
        self.assertEqual("Unzip [aaab.zip] into [aaab_17-11-2026-10-00-00/].", content.last_action_description)

        content.zip_unzip()  # pressed again while the first unzip is still running
        self.assertEqual(1, mock_fs.claim_unique_name.call_count)

    @mock.patch('content.file_system')
    def test_background_messages_never_pile_up(self, mock_fs):
        content = self.make_content(mock_fs)
        for i in range(3):
            content.describe_last_action("Action {}.", i)
            content.report_from_background("old", "Failure {}.".format(i))
        self.assertEqual("Action 2. | Failure 2.", content.last_action_description)
        content.report_from_background("old", "Failure 3.")  # two failures in a row: still just two parts
        self.assertEqual("Action 2. | Failure 3.", content.last_action_description)

    @mock.patch('content.file_system')
    def test_names_containing_the_separator_survive(self, mock_fs):
        content = self.make_content(mock_fs)
        content.describe_last_action("Renamed [{}] to [{}].", "x", "a | b")
        content.report_from_background("old", "Zip of [y] failed.")
        self.assertEqual("Renamed [x] to [a | b]. | Zip of [y] failed.", content.last_action_description)

    @mock.patch('content.file_system')
    def test_fully_successful_batch_delete_wording(self, mock_fs):
        content = self.make_content(mock_fs)
        content.marked_item_indices = [0, 1]
        mock_fs.delete.side_effect = [('aaaa', cwd + 'aaaa'), ('aaab.zip', cwd + 'aaab.zip')]
        content.delete()
        self.assertEqual("Deleted 2 files.", content.last_action_description)

    @mock.patch('content.file_system')
    def test_every_distinct_delete_error_is_reported(self, mock_fs):
        content = self.make_content(mock_fs)
        content.marked_item_indices = [0, 1]
        mock_fs.delete.side_effect = [FileSystemError("No permission"), FileSystemError("Device busy")]
        content.delete()
        self.assertEqual("No permission; Device busy: no files deleted.", content.last_action_description)

    @mock.patch('content.file_system')
    def test_partly_failed_batch_delete_reports_both(self, mock_fs):
        content = self.make_content(mock_fs)
        content.marked_item_indices = [0, 1]
        mock_fs.delete.side_effect = [('aaaa', cwd + 'aaaa'), FileSystemError("No permission to delete")]
        content.delete()
        self.assertEqual("Deleted 1 of 2 files; the rest failed: No permission to delete.",
                         content.last_action_description)

    @mock.patch('content.threading.Thread', SyncThread)
    @mock.patch('content.file_system')
    def test_confirmed_clipboard_copy_is_shown(self, mock_fs):
        content = self.make_content(mock_fs)
        mock_fs.copy_with_clipboard_tools.return_value = True
        content.copy_name_to_clipboard()
        self.assertEqual("Copied [aaaa] to clipboard.", content.last_action_description)
        self.assertFalse(content.send_pending_osc52())

    @mock.patch('content.threading.Thread', SyncThread)
    @mock.patch('content.file_system')
    def test_without_tools_the_main_thread_sends_osc52(self, mock_fs):
        content = self.make_content(mock_fs)
        mock_fs.copy_with_clipboard_tools.return_value = False
        content.copy_name_to_clipboard()
        mock_fs.copy_via_osc52.assert_not_called()  # never from the background thread
        with mock.patch('content.platform_utils.clipboard_install_hint',
                        return_value="Install wl-clipboard, xclip or xsel"):
            self.assertTrue(content.send_pending_osc52())
        mock_fs.copy_via_osc52.assert_called_once_with('aaaa')
        self.assertIn("Install wl-clipboard, xclip or xsel", content.last_action_description)

    @mock.patch('content.threading.Thread', SyncThread)
    @mock.patch('content.file_system')
    def test_clipboard_failure_is_shown(self, mock_fs):
        content = self.make_content(mock_fs)
        mock_fs.copy_with_clipboard_tools.return_value = False
        mock_fs.copy_via_osc52.side_effect = FileSystemError("No clipboard tool found")
        content.copy_name_to_clipboard()
        content.send_pending_osc52()
        self.assertEqual("Could not copy [aaaa]: No clipboard tool found.", content.last_action_description)

    @mock.patch('content.threading.Thread', SyncThread)
    @mock.patch('content.logging')
    @mock.patch('content.file_system')
    def test_failing_cleanup_does_not_escape_the_thread(self, mock_fs, _logging):
        content = self.make_content(mock_fs)

        def cleanup():
            raise OSError("cleanup broke")

        content.run_in_background("Work failed.", mock.Mock(side_effect=OSError), on_failure=cleanup)
        self.assertEqual("Work failed.", content.last_action_description)

    @mock.patch('content.file_system')
    def test_failed_undo_does_not_crash(self, mock_fs):
        content = self.make_content(mock_fs)
        content.save_deletion_info(('aaaa', cwd + 'aaaa'))
        mock_fs.restore_from_trash.side_effect = FileSystemError("It is no longer in the trash")
        mock_fs.is_in_trash.return_value = False
        content.undo()
        self.assertEqual("Could not restore [aaaa]: It is no longer in the trash.", content.last_action_description)

    @mock.patch('content.file_system')
    def test_delete_that_cannot_be_undone_says_so(self, mock_fs):
        content = self.make_content(mock_fs)
        mock_fs.delete.return_value = None
        content.delete()
        self.assertIn("undo is not available", content.last_action_description)
        self.assertEqual(0, len(content.trash_undo_stack))

    @mock.patch('content.logging')
    @mock.patch('content.threading.Thread')
    @mock.patch('content.file_system')
    def test_failed_zip_is_reported_and_does_not_block_further_zips(self, mock_fs, thread, _logging):
        content = self.make_content(mock_fs)
        mock_fs.zip_items.side_effect = OSError("disk full")
        mock_fs.claim_unique_name.return_value = "aaaa"
        content.zip_selected_item()
        self.assertEqual("aaaa", content.pending_zip_name)

        thread.call_args.kwargs['target']()  # run the background task here

        self.assertEqual("", content.pending_zip_name)
        self.assertFalse(content.archive_busy)
        self.assertEqual("Zip of [aaaa] failed.", content.last_action_description)


class TestTrashRoundTrip(unittest.TestCase):
    """Uses a real temporary folder as both the working folder and the trash."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.trash = os.path.join(self.root, 'trash') + '/'
        patcher = mock.patch('file_system.get_users_trash_path', return_value=self.trash)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('file_system._uses_freedesktop_trash', return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.root, True)

    def touch(self, name):
        path = os.path.join(self.root, name)
        open(path, 'w').close()
        return path

    def test_delete_and_restore(self):
        path = self.touch('f')
        trashed_name, original = file_system.delete(path)
        self.assertFalse(os.path.exists(path))
        file_system.restore_from_trash(trashed_name, original)
        self.assertTrue(os.path.exists(path))

    def test_name_collision_in_trash_gets_unique_name(self):
        first_name, _ = file_system.delete(self.touch('f'))
        second_name, original = file_system.delete(self.touch('f'))
        self.assertNotEqual(first_name, second_name)
        file_system.restore_from_trash(second_name, original)
        self.assertTrue(os.path.exists(original))

    def test_repeated_collisions_never_overwrite_trashed_items(self):
        names = [file_system.delete(self.touch('f'))[0] for _ in range(4)]
        self.assertEqual(4, len(set(names)))
        self.assertEqual(4, len(os.listdir(self.trash)))

    def test_orphaned_trashinfo_is_not_overwritten(self):
        info_dir = os.path.join(self.root, 'info') + '/'
        os.makedirs(info_dir)
        open(info_dir + 'f.trashinfo', 'w').close()
        with mock.patch('file_system._uses_freedesktop_trash', return_value=True), \
                mock.patch('file_system._trash_info_dir', return_value=info_dir):
            trashed_name, _ = file_system.delete(self.touch('f'))
        self.assertNotEqual('f', trashed_name)
        self.assertEqual(0, os.path.getsize(info_dir + 'f.trashinfo'))

    def test_trashinfo_path_is_percent_encoded(self):
        info_dir = os.path.join(self.root, 'info') + '/'
        with mock.patch('file_system._uses_freedesktop_trash', return_value=True), \
                mock.patch('file_system._trash_info_dir', return_value=info_dir):
            trashed_name, original = file_system.delete(self.touch('100% é.txt'))
        with open(info_dir + trashed_name + '.trashinfo') as f:
            info = f.read()
        self.assertIn('Path=' + original.replace('%', '%25').replace(' ', '%20').replace('é', '%C3%A9'), info)

    @mock.patch('file_system._delete_via_finder', return_value=True)
    @mock.patch('file_system._uses_freedesktop_trash', return_value=False)
    def test_finder_is_used_only_for_the_macos_privacy_block(self, _freedesktop, finder):
        import errno
        path = self.touch('f')
        with mock.patch('file_system.shutil.move', side_effect=PermissionError(errno.EACCES, 'denied')):
            with self.assertRaises(FileSystemError):
                file_system.delete(path)
        finder.assert_not_called()
        eperm = PermissionError(errno.EPERM, 'not permitted')
        # EPERM for another reason (sticky folder, immutable file) while the Trash itself is readable
        with mock.patch('file_system.shutil.move', side_effect=eperm), \
                mock.patch('file_system._trash_folder_unreadable', return_value=False):
            with self.assertRaises(FileSystemError):
                file_system.delete(path)
        finder.assert_not_called()
        # the privacy block: the Trash folder itself cannot be read; it can show up as EPERM or EACCES
        for error in (eperm, PermissionError(errno.EACCES, 'denied')):
            with mock.patch('file_system.shutil.move', side_effect=error), \
                    mock.patch('file_system._trash_folder_unreadable', return_value=True):
                self.assertIsNone(file_system.delete(path))
        self.assertEqual(2, finder.call_count)

    def test_undo_does_not_restore_a_different_item_that_took_the_same_name(self):
        info_dir = os.path.join(self.root, 'info') + '/'
        with mock.patch('file_system._uses_freedesktop_trash', return_value=True), \
                mock.patch('file_system._trash_info_dir', return_value=info_dir):
            trashed_name, original = file_system.delete(self.touch('report'))
            # emptied elsewhere, then an unrelated 'report' is trashed under the same name
            os.remove(self.trash + trashed_name)
            os.remove(info_dir + trashed_name + '.trashinfo')
            open(self.trash + trashed_name, 'w').close()
            with open(info_dir + trashed_name + '.trashinfo', 'w') as f:
                f.write('[Trash Info]\nPath=/somewhere/else/report\n')
            with self.assertRaises(FileSystemError):
                file_system.restore_from_trash(trashed_name, original)
        self.assertTrue(os.path.exists(self.trash + trashed_name))

    def test_trash_name_claimed_by_someone_else_meanwhile_is_skipped(self):
        info_dir = os.path.join(self.root, 'info') + '/'
        real_write = file_system._write_trashinfo
        calls = []

        def racing_write(name, original):
            calls.append(name)
            if len(calls) == 1:  # another program claims the name first
                real_write(name, '/other/program/item')
            real_write(name, original)

        with mock.patch('file_system._uses_freedesktop_trash', return_value=True), \
                mock.patch('file_system._trash_info_dir', return_value=info_dir), \
                mock.patch('file_system._write_trashinfo', side_effect=racing_write):
            trashed_name, _ = file_system.delete(self.touch('f'))
        self.assertNotEqual('f', trashed_name)
        with open(info_dir + 'f.trashinfo') as f:
            self.assertIn('/other/program/item', f.read())

    def test_failed_move_leaves_no_orphan_copy_in_the_trash(self):
        path = self.touch('f')
        info_dir = os.path.join(self.root, 'info') + '/'

        def copy_then_fail(src, dst):
            shutil.copy2(src, dst)  # like a move across disks: copied, then removing the original fails
            raise PermissionError(13, 'cannot remove original')

        with mock.patch('file_system._uses_freedesktop_trash', return_value=True), \
                mock.patch('file_system._trash_info_dir', return_value=info_dir), \
                mock.patch('file_system.shutil.move', side_effect=copy_then_fail):
            with self.assertRaises(FileSystemError):
                file_system.delete(path)
        self.assertTrue(os.path.exists(path))
        self.assertEqual([], os.listdir(self.trash))
        self.assertEqual([], os.listdir(info_dir))

    def test_rename_onto_an_existing_folder_is_refused(self):
        path = self.touch('a')
        os.makedirs(os.path.join(self.root, 'docs'))
        with self.assertRaises(FileSystemError) as raised:
            file_system.rename(path, os.path.join(self.root, 'docs'))
        self.assertEqual("Destination already exists", raised.exception.message)
        self.assertTrue(os.path.exists(path))

    def test_rename_onto_a_broken_link_is_refused_not_a_crash(self):
        path = self.touch('a')
        os.symlink('/nonexistent', os.path.join(self.root, 'notes'))
        with self.assertRaises(FileSystemError):
            file_system.rename(path, os.path.join(self.root, 'notes'))

    def test_rename_onto_a_link_to_the_item_is_refused(self):
        path = self.touch('report')
        os.symlink(path, os.path.join(self.root, 'latest'))
        with self.assertRaises(FileSystemError):
            file_system.rename(path, os.path.join(self.root, 'latest'))
        self.assertTrue(os.path.islink(os.path.join(self.root, 'latest')))

    def test_names_that_are_not_valid_utf8_can_be_deleted_and_restored(self):
        info_dir = os.path.join(self.root, 'info') + '/'
        name = os.fsdecode(b'caf\xe9')  # Latin-1 bytes, not valid UTF-8
        with mock.patch('file_system._uses_freedesktop_trash', return_value=True), \
                mock.patch('file_system._trash_info_dir', return_value=info_dir):
            trashed_name, original = file_system.delete(self.touch(name))
            file_system.restore_from_trash(trashed_name, original)
        self.assertTrue(os.path.exists(original))

    def test_rename_to_the_same_name_does_nothing(self):
        path = self.touch('a')
        file_system.rename(path, path)
        self.assertTrue(os.path.exists(path))

    def test_failed_folder_copy_into_the_trash_leaves_no_partial_copy(self):
        folder = os.path.join(self.root, 'd')
        os.makedirs(folder)
        open(os.path.join(folder, 'f'), 'w').close()
        info_dir = os.path.join(self.root, 'info') + '/'

        def copy_partly_then_fail(src, dst):
            os.makedirs(dst)  # like copytree across disks: part copied, then an unreadable file
            raise shutil.Error([(src, dst, 'unreadable')])

        with mock.patch('file_system._uses_freedesktop_trash', return_value=True), \
                mock.patch('file_system._trash_info_dir', return_value=info_dir), \
                mock.patch('file_system.shutil.move', side_effect=copy_partly_then_fail):
            with self.assertRaises(FileSystemError) as raised:
                file_system.delete(folder + '/')
        self.assertEqual("Some files could not be copied", raised.exception.message)
        self.assertEqual([], os.listdir(self.trash))
        self.assertEqual([], os.listdir(info_dir))
        self.assertTrue(os.path.exists(os.path.join(folder, 'f')))

    def test_claimed_names_are_created_and_never_reused(self):
        folder = self.root + '/'
        first = file_system.claim_unique_name(folder, 'x', '.zip')
        second = file_system.claim_unique_name(folder, 'x', '.zip')
        self.assertNotEqual(first, second)
        self.assertTrue(os.path.isfile(folder + first + '.zip'))
        new_folder = file_system.claim_unique_name(folder, 'x', make_folder=True)
        self.assertTrue(os.path.isdir(folder + new_folder))

    def test_restore_refuses_to_overwrite(self):
        trashed_name, original = file_system.delete(self.touch('f'))
        self.touch('f')
        with self.assertRaises(FileSystemError):
            file_system.restore_from_trash(trashed_name, original)


class TestZipItems(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)

    def unzipped_names(self, archive):
        out = os.path.join(self.root, 'out')
        shutil.unpack_archive(archive, out, 'zip')
        return sorted(os.path.relpath(os.path.join(d, f), out)
                      for d, _, files in os.walk(out) for f in files)

    def test_single_file(self):
        path = os.path.join(self.root, 'f.txt')
        open(path, 'w').close()
        archive = os.path.join(self.root, 'f.zip')
        file_system.zip_items([path], archive)
        self.assertEqual(['f.txt'], self.unzipped_names(archive))

    def test_folder_contents_only(self):
        os.makedirs(os.path.join(self.root, 'd'))
        open(os.path.join(self.root, 'd', 'b'), 'w').close()
        archive = os.path.join(self.root, 'd.zip')
        file_system.zip_items([os.path.join(self.root, 'd') + '/'], archive, contents_only=True)
        self.assertEqual(['b'], self.unzipped_names(archive))

    def test_pipes_broken_links_and_link_loops_do_not_break_or_hang(self):
        d = os.path.join(self.root, 'd')
        os.makedirs(os.path.join(d, 'real'))
        open(os.path.join(d, 'real', 'f'), 'w').close()
        os.mkfifo(os.path.join(d, 'pipe'))
        os.symlink('/nonexistent', os.path.join(d, 'broken'))
        os.symlink(d, os.path.join(d, 'real', 'loop'))     # link back up: a loop
        os.symlink(os.path.join(d, 'real'), os.path.join(d, 'alias'))  # link to a folder
        archive = os.path.join(self.root, 'x.zip')
        file_system.zip_items([d + '/'], archive)
        names = self.unzipped_names(archive)
        self.assertEqual(['d/real/f'], names)  # no pipe, no broken link, inside links not duplicated

    def test_links_to_folders_are_not_followed(self):
        os.makedirs(os.path.join(self.root, 'shared'))
        open(os.path.join(self.root, 'shared', 'lib.py'), 'w').close()
        os.makedirs(os.path.join(self.root, 'proj'))
        os.symlink(os.path.join(self.root, 'shared'), os.path.join(self.root, 'proj', 'lib'))
        archive = os.path.join(self.root, 'p.zip')
        file_system.zip_items([os.path.join(self.root, 'proj') + '/'], archive)
        self.assertEqual([], self.unzipped_names(archive))

    def test_unreadable_subfolder_fails_the_zip_clearly(self):
        if os.geteuid() == 0:
            self.skipTest("root can read everything")
        locked = os.path.join(self.root, 'd', 'locked')
        os.makedirs(locked)
        os.chmod(locked, 0)
        self.addCleanup(os.chmod, locked, 0o755)
        with self.assertRaises(FileSystemError) as raised:
            file_system.zip_items([os.path.join(self.root, 'd') + '/'], os.path.join(self.root, 'x.zip'))
        self.assertIn('Cannot read', raised.exception.message)

    def test_selected_broken_link_or_folder_link_is_refused(self):
        os.symlink('/nonexistent', os.path.join(self.root, 'broken'))
        os.symlink(self.root, os.path.join(self.root, 'here'))
        for name in ('broken', 'here'):
            with self.assertRaises(FileSystemError):
                file_system.zip_items([os.path.join(self.root, name)], os.path.join(self.root, name + '.zip'))

    def test_files_dated_before_1980_can_be_zipped(self):
        path = os.path.join(self.root, 'old.txt')
        open(path, 'w').close()
        os.utime(path, (0, 0))
        archive = os.path.join(self.root, 'old.zip')
        file_system.zip_items([path], archive)
        self.assertEqual(['old.txt'], self.unzipped_names(archive))

    def test_unique_name_keeps_extension_last(self):
        open(os.path.join(self.root, 'a.zip'), 'w').close()
        name = file_system.unique_name_in(self.root + '/', 'a', '.zip')
        self.assertTrue(name.startswith('a_'))
        self.assertFalse(os.path.exists(os.path.join(self.root, name + '.zip')))

    def test_file_and_folder_keep_their_names(self):
        open(os.path.join(self.root, 'a'), 'w').close()
        os.makedirs(os.path.join(self.root, 'd', 'sub'))
        open(os.path.join(self.root, 'd', 'sub', 'b'), 'w').close()
        archive = os.path.join(self.root, 'x.zip')
        file_system.zip_items([os.path.join(self.root, 'a'), os.path.join(self.root, 'd') + '/'], archive)
        self.assertEqual(['a', 'd/sub/b'], self.unzipped_names(archive))


if __name__ == '__main__':
    unittest.main()
