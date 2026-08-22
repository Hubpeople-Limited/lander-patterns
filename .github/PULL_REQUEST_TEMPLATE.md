## What this adds or changes

<!-- One or two sentences: which pattern, and what it is for. -->

## Checklist

- [ ] The pattern is a folder under `patterns/` with all four files
      (`pattern.html`, `pattern.css`, `README.md`, `preview-content.json`)
- [ ] The metadata header is complete (CONTRIBUTING.md has the shape)
- [ ] Every selector in `pattern.css` references the pattern's own class
      (see CONTRIBUTING)
- [ ] No scripts, no inline styles, no hardcoded colours/radii/shadows —
      tokens only
- [ ] `needs` states the real content the pattern consumes, and every need
      has a slot
- [ ] If this changes an existing pattern's CSS or structure: `version` bumped
- [ ] I looked at both preview renders — the checks attach them to this PR as
      the `pattern-previews` artifact — and both feels look intentional
