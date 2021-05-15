import unittest
from unittest import mock

from content import Content

cwd = '/a/aa/aac/'
parent_dir = '/a/aa/'
mock_directory_contents = {cwd: [], parent_dir: ['aaa/', 'aab/', 'aac/']}


def mock_return_values(arg):
    return mock_directory_contents[arg]


class TestEmptyFolder(unittest.TestCase):

    @mock.patch('content.terminal')
    def test_delete_is_not_called_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.delete_selected()

        mock_terminal.delete.assert_not_called()

    @mock.patch('content.terminal')
    def test_cut_is_not_started_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.cut_selected()

        self.assertEqual('', content.path_to_copy)

    @mock.patch('content.terminal')
    def test_copy_is_not_started_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.copy_selected()

        self.assertEqual('', content.path_to_copy)

    @mock.patch('content.terminal')
    def test_rename_is_not_called_when_folder_is_empty(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()

        content.rename('a', 'b')

        mock_terminal.move.assert_not_called()


if __name__ == '__main__':
    unittest.main()
