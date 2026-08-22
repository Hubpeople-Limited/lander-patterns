"""Ways to make text unreadable that the other checks wave through.

A contrast ratio cannot be computed in this repository, because the tokens
belong to the brand rather than to us. So the guarantee the contract gives is
only ever as good as the ink being used at full strength on a ground the
contract covers. These are the routes that quietly take that away, and each
one has shipped somewhere before it was checked for.
"""
import re

RULE = re.compile(r"([^{}]*)\{([^{}]*)\}")


def _rules(css):
    """(selector, body, line) for every rule.

    @keyframes blocks are dropped whole: `from { opacity: 0 }` is a starting
    frame, not a state the page can be left in, and reading one as a rule
    reports every honest animation as hidden content."""
    stripped = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    stripped = re.sub(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\}\s*)*\}", "",
                      stripped)
    for m in RULE.finditer(stripped):
        selector = m.group(1).strip()
        line = stripped[:m.start()].count("\n") + 1
        yield selector, m.group(2), line


def check(css, report):
    """`report(detail)` is called once per finding."""
    for selector, body, line in _rules(css):
        # A partial fade on text. The token promises 4.5:1 and opacity
        # silently divides it, so the guarantee stops holding at the exact
        # point somebody thought they were being subtle.
        faded = re.search(r"(?<![-\w])opacity\s*:\s*(0?\.\d+)", body)
        if faded and re.search(r"(?<![-\w])color\s*:", body):
            report(f"line {line}: opacity {faded.group(1)} on a rule that "
                   "also sets color - dim with --color-text-soft, which "
                   "carries a guarantee, not with opacity, which removes one")

        # The same move wearing the contract's clothes: color-mix() of
        # contract tokens is blessed, and `transparent` is not a colour
        # literal, so this reads as compliant and is not.
        if re.search(r"(?<![-\w])color\s*:[^;]*color-mix\([^;]*transparent",
                     body):
            report(f"line {line}: text colour mixed toward transparent - "
                   "the result carries no guarantee, whatever went into it")

    # Content hidden by default is legitimate when this same stylesheet can
    # reveal it again - a carousel card waiting on :checked needs no script.
    # It is not legitimate when only the behaviour library's injected classes
    # bring it back, because then the no-JS render is missing content.
    revealed = set()
    for selector, body, _ in _rules(css):
        if "hub-" in selector:
            continue
        if re.search(r"(?<![-\w])(opacity\s*:\s*1|visibility\s*:\s*visible)",
                     body):
            revealed.update(re.findall(r"\.([\w-]+)", selector))

    for selector, body, line in _rules(css):
        if "hub-" in selector:
            continue
        hidden = re.search(
            r"(?<![-\w])(opacity\s*:\s*0(?![.\d])|visibility\s*:\s*hidden)",
            body)
        if not hidden:
            continue
        # A modifier reveals its base: `.card` hidden and `.card--1` shown is
        # one mechanism, not two, so match on prefix rather than equality.
        hidden_classes = re.findall(r"\.([\w-]+)", selector)
        if any(r == h or r.startswith(h + "--")
               for h in hidden_classes for r in revealed):
            continue
        report(f"line {line}: '{hidden.group(1).strip()}' with nothing in "
               "this stylesheet to reveal it - the no-JS render is the page, "
               "so content may not wait for a script")
