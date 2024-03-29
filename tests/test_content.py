import unittest
from unittest import mock

from content import Content
from fs_item import FsItem

cwd = '/a/aa/aac/'
parent_dir = '/a/aa/'
mock_directory_contents = {cwd: ['aaaa', 'aaab', 'aaac'], parent_dir: ['aaa/', 'aab/', 'aac/']}


def mock_return_values(arg):
    return list(map(lambda vl: FsItem(vl), mock_directory_contents[arg]))


class TestContent(unittest.TestCase):

    def test_path_with_slash_has_last_element_word(self):
        path_with_slash = "/aaa/bbb/"
        content = Content()
        last_element = content.to_path_elements(path_with_slash)[-1]

        self.assertEqual("bbb", last_element)

    def test_path_without_slash_has_last_element_word(self):
        path_with_slash = "/aaa/bbb"
        content = Content()
        last_element = content.to_path_elements(path_with_slash)[-1]

        self.assertEqual("bbb", last_element)

    @mock.patch('content.file_system')
    def test_second_line_is_selected_when_selecting_below_the_first_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.down()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, 1)

    @mock.patch('content.file_system')
    def test_first_line_is_marked_when_marking_it(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.toggle_mark_item()
        content.recalculate_content()

        self.assertEqual(content.marked_item_indices, [0])

    @mock.patch('content.file_system')
    def test_second_line_is_marked_when_marking_it_after_marking_first_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.toggle_mark_item()
        content.recalculate_content()
        content.down()
        content.toggle_mark_item()
        content.recalculate_content()

        self.assertEqual(content.marked_item_indices, [0, 1])

    @mock.patch('content.file_system')
    def test_first_line_is_UNmarked_when_UNmarking_it(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.toggle_mark_item()
        content.recalculate_content()
        content.toggle_mark_item()
        content.recalculate_content()

        self.assertEqual(content.marked_item_indices, [])

    @mock.patch('content.file_system')
    def test_penultimate_line_is_selected_when_selecting_above_the_last_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = content.get_num_main_lines() - 1

        content.up()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, content.get_num_main_lines() - 2)

    @mock.patch('content.file_system')
    def test_first_line_is_selected_when_selecting_below_the_last_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = content.get_num_main_lines() - 1

        content.down()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, 0)

    @mock.patch('content.file_system')
    def test_last_line_is_selected_when_selecting_above_the_first_line(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 0

        content.up()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, content.get_num_main_lines() - 1)

    @mock.patch('content.file_system')
    def test_same_line_is_selected_after_deleting_selected(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 1

        content.delete()
        content.recalculate_content()

        self.assertEqual(content.main_pane_selected_line_i, 1)

    @mock.patch('content.file_system')
    def test_pasted_line_is_selected_after_pasting(self, mock_terminal):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        content = Content()
        content.main_pane_selected_line_i = 1

        mock_directory_contents_during_paste = {cwd: ['aaaa', 'aaab', 'aaac', 'bbbb'],
                                                parent_dir: ['aaa/', 'aab/', 'aac/']}

        def mock_return_values_during_paste(arg):
            return list(map(lambda vl: FsItem(vl), mock_directory_contents_during_paste[arg]))

        mock_terminal.list_all_in.side_effect = mock_return_values_during_paste
        content.paths_to_copy = ['/b/bb/bbb/bbbb']

        content.paste()

        self.assertEqual(content.main_pane_selected_line_i, 3)


if __name__ == '__main__':
    unittest.main()
