"""
    A file system item that is a folder or a file with its properties.
"""


class FsItem:

    def __init__(self, text):
        self.text = text
        self.is_marked = False

    def __eq__(self, other):
        if isinstance(other, FsItem):
            return self.text == other.text
        return False

    def is_folder(self):
        return self.text.endswith("/")

    # cleans the slash in the end, which folders have
    def get_clean_name(self):
        return self.text[:-1] if self.is_folder() else self.text
