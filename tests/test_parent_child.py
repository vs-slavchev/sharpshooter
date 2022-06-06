import unittest
from unittest import mock

from content import Content
from fs_item import FsItem

cwd = '/a/aa/aac/'
parent_dir = '/a/aa/'
child_dir = '/a/aa/aac/aaaa/'
mock_directory_contents = {cwd: ['aaaa/', 'aaab/', 'aaac/'], parent_dir: ['aaa/', 'aab/', 'aac/'], child_dir: ['aaaaa']}


def mock_return_values(arg):
    return list(map(lambda vl: FsItem(vl), mock_directory_contents[arg]))


class TestContent(unittest.TestCase):

    @mock.patch('content.terminal')
    def test_all_marked_lines_are_unmarked_when_opening_child_folder(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.toggle_mark_item()
        content.recalculate_content()
        content.open_child()
        content.recalculate_content()

        self.assertEqual([], content.marked_item_indices)


if __name__ == '__main__':
    unittest.main()
