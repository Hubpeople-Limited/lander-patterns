# Image placeholders

Stand-ins for a photograph a page does not have yet. A build places one where
an image slot has no fitting picture, so a page can be photo-led before the
brand's photography exists.

## The set

Twenty line pictograms: five subjects (`couple`, `person`, `group`, `place`,
`object`) in four crops (`wide` 16:9, `landscape` 4:3, `portrait` 3:4,
`square`). Each is a mid-grey line drawing on a transparent ground with a small
"Photo to come" mark.

`ci/make_placeholders.py` draws them; CI fails if a file here differs from
what it draws. Each is uploaded to the CDN once, and `placeholders.json`
records its URL and hash. **Every brand references the CDN URL**; nothing is
copied into a brand or uploaded again. Editing a drawing means running the
script, uploading the changed files and recording their new URLs.

## Recording a new upload

Each `placeholders.json` entry is keyed `<subject>/<crop>` and holds
`{"file", "url", "sha256", "width", "height"}`. `sha256` is
`lint.placeholder_digest(path)` - the SHA-256 of the file with CRLF line
endings normalised to LF, so a checkout that turns LF into CRLF is not read
as a changed file.

## How a build uses one

- The pattern's `image-slots` line says what a slot needs. A build with no
  fitting picture takes the first subject listed, in the slot's crop.
- The image is marked `data-hub-placeholder="<slot> · <subject> · <crop>"`
  and carries `alt=""`: it shows nothing yet.
- `srcset` and `sizes` are removed from a placeholder image.
- The pattern paints the brand's colour behind a placeholder, so one file
  reads in every brand's colours.
- At avatar size - a few dozen pixels - the drawing and its mark are too
  small to read, and a placeholder there shows as no more than a tinted
  disc. What marks it at that size is the build's own list of what it
  placed, not the image.
- A slot marked `placeholder=no` never takes one. A placeholder never fills
  a slot that shows a member, a testimonial or anyone presented as proof:
  those patterns are `consented-people`, and every slot on them is
  `placeholder=no`.

## What it is not

- Not a person. The drawings are pictograms so that nothing reads as an
  invented member.
- Not a quiet substitute. The build lists every placeholder it placed and
  says what photograph each one is waiting for.

`wide.svg`, `landscape.svg` and `portrait.svg` are the earlier stand-ins,
still read by `ci/build_configurator.py`. New work uses the set above.
