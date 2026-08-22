"""Text handling shared by more than one gate module."""

import re


def blank_comments(text):
    """Comments removed, newlines kept.

    Replacing a comment with a single space destroys the newlines
    inside it, which moves the reported line of everything after a
    multi-line comment - and both callers report line numbers.
    """
    return re.sub("/[*].*?[*]/",
                  lambda m: re.sub("[^" + chr(10) + "]", " ", m.group(0)),
                  text, flags=re.S)
