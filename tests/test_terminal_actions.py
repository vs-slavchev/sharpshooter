import unittest
from unittest import mock

from content import Content
from fs_item import FsItem

cwd = '/a/aa/aac/'
parent_dir = '/a/aa/'
mock_directory_contents = {cwd: ['aaaa', 'aaab', 'aaac'], parent_dir: ['aaa/', 'aab/', 'aac/']}


def mock_return_values(arg):
    return list(map(lambda vl: FsItem(vl), mock_directory_contents[arg]))


class TestTerminalActions(unittest.TestCase):

    @mock.patch('content.file_system')
    def test_open_terminal_is_called_with_cwd(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.open_new_terminal()

        mock_terminal.open_new_terminal.assert_called_with(content.cwd)

    @mock.patch('content.file_system')
    def test_cut_changes_path_to_copy_and_copy_removes_source(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.cut()

        self.assertEqual([cwd + 'aaaa'], content.paths_to_copy)
        self.assertTrue(content.copy_removes_source)

    @mock.patch('content.file_system')
    def test_copy_changes_path_to_copy_and_copy_removes_source(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.copy()

        self.assertEqual([cwd + 'aaaa'], content.paths_to_copy)
        self.assertFalse(content.copy_removes_source)

    @mock.patch('content.file_system')
    def test_delete_calls_delete_with_child_path(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.delete()

        mock_terminal.delete.assert_called_with(cwd + 'aaaa')

    @mock.patch('content.file_system')
    def test_rename_is_called_with_correct_absolute_paths(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_lines = [FsItem('aaaa')]

        content.rename('bbbb')

        mock_terminal.move.aassert_called_with(cwd + 'aaaa', cwd + 'bbbb')


if __name__ == '__main__':
    unittest.main()
