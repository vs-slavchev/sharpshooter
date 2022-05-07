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


def fit_text_to_line_length(available_width, text):
    available_width = available_width - 1
    indicator_long_line = "..."
    if len(text) > available_width:
        last_char_index = available_width - len(indicator_long_line)
        text = text[:last_char_index] + indicator_long_line
    return text
