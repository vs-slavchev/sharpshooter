import unittest
from unittest import mock

from content import Content
from fs_item import FsItem

cwd = '/a/aa/aac/'
parent_dir = '/a/aa/'
mock_directory_contents = {cwd: ['aaaa', 'aaab', 'aaac'], parent_dir: ['aaa/', 'aab/', 'aac/']}


def mock_return_values(arg):
    return map(lambda vl: FsItem(vl), mock_directory_contents[arg])


class TestContent(unittest.TestCase):

    @mock.patch('content.terminal')
    def test_second_line_is_selected_when_selecting_below_the_first_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.down()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, 1)

    @mock.patch('content.terminal')
    def test_penultimate_line_is_selected_when_selecting_above_the_last_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = content.get_num_main_lines() - 1

        content.up()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, content.get_num_main_lines() - 2)

    @mock.patch('content.terminal')
    def test_first_line_is_selected_when_selecting_below_the_last_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = content.get_num_main_lines() - 1

        content.down()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, 0)

    @mock.patch('content.terminal')
    def test_last_line_is_selected_when_selecting_above_the_first_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.up()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, content.get_num_main_lines() - 1)

    @mock.patch('content.terminal')
    def test_same_line_is_selected_after_deleting_selected(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 1

        content.delete_selected()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, 1)

    @mock.patch('content.terminal')
    def test_pasted_line_is_selected_after_pasting(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.get_ls.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 1

        mock_directory_contents_during_paste = {cwd: ['aaaa', 'aaab', 'aaac', 'bbbb'],
                                                parent_dir: ['aaa/', 'aab/', 'aac/']}

        def mock_return_values_during_paste(arg):
            return map(lambda vl: FsItem(vl), mock_directory_contents_during_paste[arg])

        mock_terminal.get_ls.side_effect = mock_return_values_during_paste
        content.path_to_copy = '/b/bb/bbb/bbbb'

        content.paste()

        self.assertEqual(content.main_pane_selected_line_i, 3)


if __name__ == '__main__':
    unittest.main()
