"""The placeholder vocabulary, named once for the library.

lint.py holds patterns to it, make_placeholders.py draws from it and
build_preview.py places from it, so the three cannot drift apart: a subject
spelled one way here and another way in a pattern header is a slot that
silently gets no placeholder.
"""
import re

SUBJECTS = ("couple", "person", "group", "place", "object")
CROPS = {"wide": (1600, 900), "landscape": (1200, 900),
         "portrait": (900, 1200), "square": (1000, 1000)}
# The side the subject should sit on so the copy over or beside it stays
# clear. `top` is for a scrim or overlay that carries text at the foot.
FOCAL = ("left", "right", "center", "top")

IMAGE_SRC_SLOT = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*"slot:([\w-]+)"', re.S)

CLAUSE = re.compile(
    r"^(?P<slot>[a-z0-9*-]+) subject=(?P<subjects>[a-z]+(?:\|[a-z]+)*) "
    r"crop=(?P<crop>[a-z]+) min=(?P<min>\d+) focal=(?P<focal>[a-z]+) "
    r"placeholder=(?P<placeholder>yes|no)$")


def file_name(subject, crop):
    return f"{subject}-{crop}.svg"


def parse_image_slots(value):
    """`hero-image subject=couple|person crop=portrait min=1280 focal=center
    placeholder=yes; ...` -> a list of clause dicts, or None when any clause
    is malformed. Vocabulary is checked by lint.py, not here, so a bad word
    is reported by name rather than as an unreadable line."""
    out = []
    for clause in [c.strip() for c in value.split(";") if c.strip()]:
        m = CLAUSE.match(clause)
        if not m:
            return None
        out.append({"slot": m["slot"], "subjects": m["subjects"].split("|"),
                    "crop": m["crop"], "min": int(m["min"]),
                    "focal": m["focal"], "placeholder": m["placeholder"] == "yes"})
    return out or None


def slot_matches(declared, name):
    """`*` in a declared slot stands for a run of digits and nothing else."""
    return re.fullmatch(re.escape(declared).replace(r"\*", r"\d+"), name) is not None
