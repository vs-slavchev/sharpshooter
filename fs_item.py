"""
    A file system item that is a folder or a file with its properties.
"""

import utility


class FsItem:

    def __init__(self, text):
        self.text = text
        self.is_marked = False

    def __eq__(self, other):
        if isinstance(other, FsItem):
            return self.text == other.text
        return False

    def is_folder(self):
        return utility.is_folder(self.text)

    def is_hidden(self):
        return utility.is_hidden(self.text)

    # cleans the slash in the end, which folders have
    def get_clean_name(self):
        return self.text[:-1] if self.is_folder() else self.text

    def __str__(self) -> str:
        return "FsItem(text={}, is_marked={})".format(self.text, self.is_marked)
