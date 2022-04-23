import unittest
from unittest import mock

from content import Content
from fs_item import FsItem

cwd = '/a/aa/.aac/'  # current folder is hidden
parent_dir = '/a/aa/'
mock_directory_contents = {cwd: ['aaaa', '.aaab', 'aaac', '.aaad'], parent_dir: ['aaa/', 'aab/', '.aac/', 'aad/']}


def mock_return_values(arg):
    return map(lambda vl: FsItem(vl), mock_directory_contents[arg])


class TestHiddenFiles(unittest.TestCase):

    @mock.patch('content.terminal')
    def test_last_line_is_selected_after_hiding_hidden_files_and_last_line_was_selected(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 3
        content.show_hidden = True

        content.toggle_show_hidden()

        self.assertEqual(1, content.main_pane_selected_line_i)

    @mock.patch('content.terminal')
    def test_same_not_hidden_line_is_selected_after_hiding_hidden_files_and_its_index_changed(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 2
        content.show_hidden = True

        content.toggle_show_hidden()

        self.assertEqual(1, content.main_pane_selected_line_i)

    @mock.patch('content.terminal')
    def test_first_not_hidden_line_is_selected_after_hiding_hidden_files(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0
        content.show_hidden = True

        content.toggle_show_hidden()

        self.assertEqual(0, content.main_pane_selected_line_i)

    @mock.patch('content.terminal')
    def test_hidden_parent_line_is_still_selected_after_hiding_hidden_files(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0
        content.parent_pane_selected_line_i = 3
        content.show_hidden = True

        content.toggle_show_hidden()
        content.recalculate_content()

        self.assertEqual(2, content.parent_pane_selected_line_i)


if __name__ == '__main__':
    unittest.main()
