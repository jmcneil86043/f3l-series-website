# Output notes — Postal Series page, navigation, README structure line

Task: https://trello.com/c/PK4mjlPv   Step: https://trello.com/c/6cilqSP5
Written: 2026-09-16 by task 6aaae6a9f3bdd88cdff26df2
Design: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-design.md` § postal.html, § Navigation

## What changed

- **`postal.html` (new)** — Postal Series page, built from `schedule.html`'s head/header/footer so it
  matches the site idiom. Five `.content-card` sections, no new CSS, no images:
  1. *F3L and F5L Monthly Postal* — what a postal is, the nine-day window, Gliderscore, FAI rules,
     F5L = F3L with an electric launch, alternating months, Ryan Woebkenberg (CD) and Ed LaCroix,
     honour-system scoring. `.btn` → the RCGroups postal thread (4942041).
  2. *Current Postal* — an `.event-card` for **September 19–27, 2026 · F3L Postal**, five rounds,
     with the line that next month is F5L and that each month's dates and task come from the thread
     and by email.
  3. *How to Enter* — the one-email process, register once, same address to unsubscribe, feedback
     invited.
  4. *After-Postal Zoom Meeting* — **Sunday, September 27, 2026 · 7:00 PM PDT (10:00 PM EDT)**,
     hosted by John McNeil, meeting ID 872 8818 9436 · passcode 932925, and a `.btn`
     "Join the Zoom meeting" pointing at the real join link from the step card.
  5. *Related* — `schedule.html`, `results.html`, the 2026 series thread.
- **Navigation** — `<li><a href="postal.html">Postal Series</a></li>` inserted after the Results item
  in all seven existing pages (`index`, `schedule`, `results`, `about`, `howto`, `host`, `highstart`)
  and in `postal.html` itself with `class="active"`. Seven items now; no CSS change, the existing
  wrap/stack rules cover it.
- **`README.txt`** — `postal.html` added to the structure listing, after `results.html`.

## Decisions applied from the review (step card, 2026-09-16)

- **Zoom link, not a placeholder.** The link arrived in the card description under `## Zoom` and in a
  card comment, superseding the earlier "keep the placeholder" line. `postal.html` carries the real
  href; there is no `TODO(zoom-link)`, no `href="#"` and no "coming soon" text anywhere in the site.
  The closing task's "no Zoom placeholder remains" check applies as originally written and passes.
- **Email address obfuscated.** Rendered as plain text `F3LF5LPostal at gmail dot com`, no `mailto:`,
  matching the organisers' obfuscation in the thread.
- **"Current Postal" names its dates** — September 19–27, 2026 · F3L Postal, with the pointer at the
  thread for later months so a reader is never stranded on a stale date.

## The pull-string video — no embed (deliberate)

This task card's name mentions "the pull-string video embed in howto.html". That clause pre-dates the
design review: the card's checklist was placed from the first plan (commit 7135358), and John's
review on 2026-09-15 dropped the embed (commit aa3acf9). The spec's § Out of scope and the design's
§ howto.html both say the video's existing link is its delivery. So **`howto.html` keeps its existing
"Pull-String Control Setup Guide" link to `https://www.youtube.com/watch?v=ZSMni8FZHJ4` unchanged**;
its only edit in this task is the Postal Series nav item. Nothing further is owed on the video —
if John wants an embedded player after all, that is a new decision, not unfinished work here.

## Verification

- `python3 -m http.server` on 18089 from this worktree (what `deploy/preview.sh 18089` runs):
  all eight pages return **200** — `index`, `schedule`, `results`, `postal`, `about`, `howto`,
  `host`, `highstart`. Every local `href` out of `postal.html` (`schedule.html`, `results.html`,
  `styles.css` and the nav) returns 200.
- `grep` confirms exactly one `href="postal.html"` in each of the eight pages.
- No `TODO(zoom-link)`, `Zoom link coming soon` or `href="#"` in any page.
- `python3 -m unittest discover -s deploy/tests` — **48 tests, OK** (deploy tooling untouched).

## Pre-existing HTML observations (not introduced here, not fixed here)

A tag-balance check found three unclosed tags that are present at the step's merge-base `10fc645`
and so pre-date this step: an unclosed `<div class="content-card">` in `schedule.html`
(the Registration Information card) and in `results.html`, and an unclosed `<strong>` in `host.html`.
Browsers auto-close all three and the pages render correctly, which is why they have gone unnoticed.
`postal.html`, `index.html`, `about.html`, `howto.html` and `highstart.html` are balanced.
Out of scope for this step (the design forbids layout changes); worth a follow-up card.

## Left for the closing task

`deploy/deploy.py` dry run and recording its plan — expected: `postal.html` new plus the seven edited
pages changed, `styles.css` and `assets/` unchanged (or everything new if the server has no manifest
yet from Step 0's first live run).
