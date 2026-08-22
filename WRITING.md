# What we publish about the code

This repository is public and permanent. Four things we write are read by
strangers and cannot be taken back: **commit messages**, **pull request titles
and bodies**, **issue text**, and **comments inside `pattern.css` and
`pattern.html`** — which are not documentation at all but product, appended
into a brand's stylesheet and pasted into a page that is served to the public.

`ci/check_prose.py` enforces the part a machine can see, which is vocabulary.
Everything below that a machine cannot see is a review question.

## The shape of a good message

Take the industry convention, which is settled and worth following:

- **Subject in the imperative**, under about 50 characters. "Hold the scrim to
  the top of the text band", not "Fixed the scrim" and not "This commit fixes".
- **Blank line, then a body** wrapped at about 72 characters.
- **State the problem in the present tense, then the change.** The Git
  project's own guidance is the clearest statement of this: *"The problem
  statement that describes the status quo is written in the present tense.
  Write 'The code does X when it is given input Y', instead of 'The code used
  to do Y when given input X'."*
- **Stand alone.** The ChromiumOS guidance puts the reason precisely, for
  exactly our situation: *"For private bugs in a public repo you may need to
  be circumspect about certain details but bear in mind that the only
  information visible in public is what you put in your commit message, so it
  should be sufficient to understand/judge the commit."*

The present tense does more work than it looks. "The code does X when given
input Y" has no actor in it, so it states a defect without anyone being its
subject. That is how you get a blameless message without writing a rule about
blame.

## Never

**Anything that identifies a person by their part in the work.** Not a name,
not a role, not "the designer", "the reviewer", "whoever wrote this". A change
is described by what it does.

**Anything internal.** Hostnames, machine or account names, local paths,
internal service names, private tracker IDs, customer, partner or brand names.
A ticket reference to a private tracker is a dead link to every outside reader
and advertises internal numbering; keep it on our side.

**How the change came about.** Which review found it, what was decided in
conversation, what tooling produced it, which iteration it was. It is not
useful to anyone building a page, and it publishes how we work.

**Criticism of earlier work.** This one is ours rather than an industry
standard — most projects have no such rule. State the condition of the code,
not a failing: "the ramp fades from the card's foot" rather than "the ramp was
wrong". Google's code review guidance is the nearest published equivalent and
is worth carrying across: *"always making comments about the code and never
making comments about the developer."*

## Security fixes

Practice genuinely splits here, so this is a decision rather than a convention.

Mozilla obfuscates hard — strip the message, omit the bug number, avoid
trigger words, even bundle the fix with unrelated work. The OpenSSF takes the
opposite view: *"attackers can usually review changes made to software (in
source or executable form) and easily determine an attack. Thus, withholding
detailed information can only be helpful for a few days at most."*

**We take the cheap half and skip the theatre**, because at this size the
elaborate version would be done inconsistently or not at all:

- Describe the fix, never the weakness. No exploit path, no reproduction, no
  proof of concept in a test.
- Avoid the trigger vocabulary in public text — the checker lists it.
- The diff is the disclosure. If a change would tell an attacker where the
  hole is in every version still pinned, develop it privately and land it at
  release. GitHub's temporary private fork on a security advisory gives us
  that for free; note CI cannot reach such a fork, so it must be testable
  locally, and the deploy must not publish from it.
- After it ships, the changelog is where a vulnerability is named plainly.

## Comments are product here

Uniquely for this repository, a comment is not read only by contributors. It
is served. CWE-615 exists for this: sensitive information in source comments
lets an attacker *"map the application's structure and files, expose hidden
parts of the site, and study the fragments of code to reverse engineer the
application"*. OWASP's secure coding checklist says it in one line: *"Remove
comments in user accessible production code that may reveal backend system or
other sensitive information."*

So the rule in CONTRIBUTING.md is not a style preference. A comment in
`pattern.css` or `pattern.html` earns its place only by stopping someone
breaking the pattern. Reasoning, measurements and history go in `README.md`,
which is read at build time and never served. `pattern.html` comments are
stripped when the pattern is placed; `pattern.css` comments are not, which is
why their ceiling is the tighter one.

## Identity

Git records author and committer name and email in every object, permanently,
and GitHub renders them. No wording policy reaches that. If we do not want a
personal name or a work address published on every commit, the fix is a
`noreply` address or an organisation identity configured before the work, not
anything written in a message.

## What the checker cannot do

It matches vocabulary. It cannot see tone, and it cannot see a message that is
technically clean and still reads as a defect log — an itemised list of what
was wrong, arguing with earlier work. That shape is the common failure and it
is caught in review, not by the tool.
