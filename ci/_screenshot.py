"""A screenshot that survives the CI runner's passing capture glitch.

Now and then headless Chromium answers a screenshot of a page that is loaded
and drawn with

    Page.screenshot: Protocol error (Page.captureScreenshot):
    Unable to capture screenshot

and the same call a moment later succeeds. A check that takes screenshots then
fails on a page it never measured, and passes when the job is run again, which
teaches whoever reads it to re-run rather than read.

capture() takes that one error again, up to ATTEMPTS times in all with WAIT_MS
between, and says on stderr each time it does. Any other error is raised at
once, and so is this one when it is still there on the last attempt: a page
that cannot be captured at all is a fault to see, not to wait out.
"""

import sys

GLITCH = "Unable to capture screenshot"
ATTEMPTS = 3
WAIT_MS = 250


def capture(tab, **kwargs):
    """tab.screenshot(**kwargs), taken again on the capture glitch alone."""
    from playwright.sync_api import Error
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return tab.screenshot(**kwargs)
        except Error as error:
            if GLITCH not in str(error) or attempt == ATTEMPTS:
                raise
            print(f"  screenshot: \"{GLITCH}\" on attempt {attempt} of {ATTEMPTS}; "
                  f"taking it again in {WAIT_MS}ms", file=sys.stderr, flush=True)
            tab.wait_for_timeout(WAIT_MS)
