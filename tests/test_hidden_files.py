import unittest
from unittest import mock

from content import Content
from fs_item import FsItem

cwd = '/a/aa/.aac/'  # current folder is hidden
parent_dir = '/a/aa/'
mock_directory_contents = {cwd: ['aaaa', '.aaab', 'aaac', '.aaad'], parent_dir: ['aaa/', 'aab/', '.aac/', 'aad/']}


def mock_return_values(arg):
    return list(map(lambda vl: FsItem(vl), mock_directory_contents[arg]))


class TestHiddenFiles(unittest.TestCase):

    @mock.patch('content.ConfigManager')
    @mock.patch('content.file_system')
    def test_last_line_is_selected_after_hiding_hidden_files_and_last_line_was_selected(
            self, mock_terminal, mock_config_manager_class):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        self.set_show_hidden(mock_config_manager_class, True)
        content = Content()
        content.main_pane_selected_line_i = 3

        content.toggle_hidden()

        self.assertEqual(1, content.main_pane_selected_line_i)

    @mock.patch('content.ConfigManager')
    @mock.patch('content.file_system')
    def test_same_not_hidden_line_is_selected_after_hiding_hidden_files_and_its_index_changed(
            self, mock_terminal, mock_config_manager_class):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        self.set_show_hidden(mock_config_manager_class, True)
        content = Content()
        content.main_pane_selected_line_i = 2

        content.toggle_hidden()

        self.assertEqual(1, content.main_pane_selected_line_i)

    @mock.patch('content.ConfigManager')
    @mock.patch('content.file_system')
    def test_first_not_hidden_line_is_selected_after_hiding_hidden_files(
            self, mock_terminal, mock_config_manager_class):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        self.set_show_hidden(mock_config_manager_class, True)
        content = Content()
        content.main_pane_selected_line_i = 0

        content.toggle_hidden()

        self.assertEqual(0, content.main_pane_selected_line_i)

    @mock.patch('content.ConfigManager')
    @mock.patch('content.file_system')
    def test_hidden_parent_line_is_still_selected_after_hiding_hidden_files(
            self, mock_terminal, mock_config_manager_class):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        self.set_show_hidden(mock_config_manager_class, True)
        content = Content()
        content.main_pane_selected_line_i = 0
        content.parent_pane_selected_line_i = 3

        content.toggle_hidden()
        content.recalculate_content()

        self.assertEqual(2, content.parent_pane_selected_line_i)

    @mock.patch('content.ConfigManager')
    @mock.patch('content.file_system')
    def test_same_not_hidden_line_is_marked_after_hiding_hidden_files_and_its_index_changed(
            self, mock_terminal, mock_config_manager_class):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        self.set_show_hidden(mock_config_manager_class, True)
        content = Content()
        content.main_pane_selected_line_i = 2
        content.toggle_mark_item()

        content.toggle_hidden()

        self.assertEqual([1], content.marked_item_indices)

    @mock.patch('content.ConfigManager')
    @mock.patch('content.file_system')
    def test_hidden_line_is_UNmarked_after_hiding_hidden_files(self, mock_terminal, mock_config_manager_class):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        self.set_show_hidden(mock_config_manager_class, True)
        content = Content()
        content.main_pane_selected_line_i = 1
        content.toggle_mark_item()

        content.toggle_hidden()

        self.assertEqual([], content.marked_item_indices)

    @mock.patch('content.ConfigManager')
    @mock.patch('content.file_system')
    def test_not_hidden_marked_line_is_marked_after_showing_hidden_files_and_its_index_changed(
            self, mock_terminal, mock_config_manager_class):
        mock_terminal.provide_initial_cwd.return_value = cwd
        mock_terminal.list_all_in.side_effect = mock_return_values
        self.set_show_hidden(mock_config_manager_class, False)

        content = Content()
        content.main_pane_selected_line_i = 1
        content.toggle_mark_item()

        content.toggle_hidden()

        self.assertEqual([2], content.marked_item_indices)

    def set_show_hidden(self, mock_config_manager_class, show_hidden):
        mock_config_manager_instance = mock_config_manager_class.return_value
        mock_config_manager_instance.get_show_hidden.return_value = show_hidden


if __name__ == '__main__':
    unittest.main()
