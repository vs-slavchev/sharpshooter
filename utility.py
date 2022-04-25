"""
    Small stateless functions used in multiple places.
"""

import re
from datetime import datetime


def is_folder(line):
    return line.endswith("/")


def is_hidden(line):
    return line.startswith(".")


def extract_item_name_from_path(path):
    item_name_search = re.search('.*/([-_. a-zA-Z0-9\(\)]+/?)$', path)
    if item_name_search:
        return item_name_search.group(1)


def now():
    return datetime.now().strftime('%d-%m-%Y-%H-%M-%S')
