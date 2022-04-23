"""
    A file system item that is a folder or a file with its properties.
"""


class FsItem:

    def __init__(self, text, marked=False):
        self.text = text
        self.marked = marked

    def get_text(self):
        return self.text

    def is_marked(self):
        return self.marked

    def __eq__(self, other):
        if isinstance(other, FsItem):
            return self.text == other.text
        return False
