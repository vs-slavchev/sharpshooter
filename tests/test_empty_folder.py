import unittest
from unittest import mock

from content import Content
from fs_item import FsItem

cwd = '/a/aa/aac/'
parent_dir = '/a/aa/'
mock_directory_contents = {cwd: [], parent_dir: ['aaa/', 'aab/', 'aac/']}


def mock_return_values(arg):
    return list(map(lambda vl: FsItem(vl), mock_directory_contents[arg]))


class TestEmptyFolder(unittest.TestCase):

    @mock.patch('content.terminal')
    def test_delete_is_not_called_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.delete()

        mock_terminal.delete.assert_not_called()

    @mock.patch('content.terminal')
    def test_cut_is_not_started_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.cut()

        self.assertEqual([], content.paths_to_copy)

    @mock.patch('content.terminal')
    def test_copy_is_not_started_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.copy()

        self.assertEqual([], content.paths_to_copy)

    @mock.patch('content.terminal')
    def test_rename_is_not_called_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.rename('b')

        mock_terminal.move.assert_not_called()

    def test_fs_items_with_same_text_are_equal(self):
        first = FsItem('a')
        second = FsItem('a')

        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
