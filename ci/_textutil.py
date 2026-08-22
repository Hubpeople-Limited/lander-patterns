"""Text handling shared by more than one gate module."""

import re


def blank_comments(text):
    """Comments removed, newline count kept, no whitespace introduced.

    Two constraints pull against each other here.

    Replacing a comment with a single space destroys the newlines inside it,
    which moves the reported line of everything after a multi-line comment -
    and every caller reports line numbers.

    But replacing it with spaces introduces whitespace where CSS tokenisation
    produces none. Per CSS Syntax a comment yields no token at all, so
    `img/*c*/.hero` is the compound `img.hero`; blanking it to spaces made it
    read as a descendant selector, and the subject came out as `.hero`.

    Emitting only the newlines satisfies both: line numbers hold, and nothing
    is inserted between two things the parser would have joined.
    """
    return re.sub("/[*].*?[*]/",
                  lambda m: chr(10) * m.group(0).count(chr(10)),
                  text, flags=re.S)
