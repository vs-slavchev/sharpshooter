import unittest

from input_keys import InputKeys


class TestHotkeyGuide(unittest.TestCase):

    def test_key_not_contained_in_action_name_then_both_separate(self):
        key = 'w'
        action_name = 'up'

        actual = InputKeys.format_hotkey_description(key, action_name)

        self.assertEqual('up - w', actual)

    def test_key_contained_in_action_name_start_then_key_marked_in_action_name(self):
        key = 'u'
        action_name = 'up'

        actual = InputKeys.format_hotkey_description(key, action_name)

        self.assertEqual('(u)p', actual)

    def test_key_contained_in_action_name_end_then_key_marked_in_action_name(self):
        key = 'p'
        action_name = 'up'

        actual = InputKeys.format_hotkey_description(key, action_name)

        self.assertEqual('u(p)', actual)

    def test_key_contained_in_action_name_with_underscore_then_key_marked_in_action_name_without_underscore(self):
        key = 'm'
        action_name = 'toggle_mark_item'

        actual = InputKeys.format_hotkey_description(key, action_name)

        self.assertEqual('toggle (m)ark item', actual)


if __name__ == '__main__':
    unittest.main()
