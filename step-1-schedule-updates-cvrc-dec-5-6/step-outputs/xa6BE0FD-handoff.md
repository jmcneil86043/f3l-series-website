# Hand-off: preview the site and publish it

## Goal

Step 1 is built and verified. What is left is yours: look at the site in a browser, and if it
reads right, publish it with `deploy/deploy.py --upload`. That is the step card's "Deploy with the
system from Step 0 once the changes are reviewed".

## Current status

All four implementation items are done and committed on this branch, and the closing checks all
passed:

- **48 deploy unit tests — OK.**
- **Preview sweep — all 8 pages HTTP 200, all 30 local links/images/downloads 200, 0 broken.**
- **Deploy dry run — exit 0, plan recorded** (see "What to expect from the publish" below).
- **No Zoom placeholder anywhere.** `postal.html` carries your real join link, meeting ID and
  passcode, verbatim from the step card.

Nothing is blocked. The one thing the closing task could not do is the publish itself, which the
spec assigned to you.

## What happened

Three workers did the work: the schedule and home page content, then the Postal page and
navigation, then this closing verification. The site changed as follows, against the merge-base
`10fc645`:

- `schedule.html` — "Previous Events" is now "Completed Events"; OG F3L (Mar), International (Jun),
  Nationals (Jul) and Coastal Cooler (Aug) each read `Status: Complete` with a
  `🏆 Results on F3XVault` link; Nationals moved to July 23-24 to match F3XVault; new upcoming
  cards for **CVRC Dec 5-6 2026, Visalia** (registration open, thread + F3XVault links) and
  **PGMC Mar 6-7 2027** (details coming soon). The completed March 2026 OG F3L card was kept, per
  your review.
- `index.html` — the 2026 contest list gains the CVRC card, so the two lists agree.
- `postal.html` (new) — Postal Series page: what a postal is, the current September 19-27 F3L
  postal, how to enter, the **After-Postal Zoom meeting Sunday Sept 27 2026, 7:00 PM PDT
  (10:00 PM EDT)** with the join button, and related links.
- All 8 pages — a "Postal Series" nav item after "Results". `README.txt` — the structure line.
- `howto.html` — **no video embed**, deliberately. Your 2026-09-15 review dropped it; the existing
  "Pull-String Control Setup Guide" link is the video's place on the site and still works (200).

Two things were found but deliberately not fixed, both present at the merge-base and both outside
this step's "no layout changes" line:

1. Unclosed `<div class="content-card">` in `schedule.html` (Registration Information) and in
   `results.html`, and an unclosed `<strong>` in `host.html`. Browsers auto-close all three and the
   pages render correctly.
2. A dead link in `howto.html`: `armsoar.com/products/e-medina-2-2m-almost-ready-to-fly` → 404.

Both are worth a follow-up card; neither should hold up the publish.

## Files & paths

All paths relative to this worktree.

| Path | What |
|---|---|
| `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-spec.md` | spec |
| `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-design.md` | design |
| `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-risks.md` | risks |
| `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/x7Fg5RiT-output-notes.md` | schedule + home page notes |
| `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/PK4mjlPv-output-notes.md` | postal page + nav notes |
| `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/xa6BE0FD-output-notes.md` | **closing checks, full detail** |
| `postal.html` | the new page |
| `schedule.html`, `index.html` | the content changes |
| `deploy/README.md` | preview and deploy reference |

## Pending checklist items

- `[needs-you] Try the new functions yourself` — this hand-off.

Every other item on the step's Tasks checklist is done.

## Open decisions

(none)

## The ask

**Preview the site, then publish it.**

```sh
deploy/preview.sh                     # http://127.0.0.1:8080/
```

From your Mac against Bishop, forward the port first: `ssh -L 8080:127.0.0.1:8080 bishop`, then
open http://localhost:8080/. Worth a look in particular:

- **Schedule** — the four completed contests and their results links, the CVRC card, the 2027 PGMC
  card.
- **Postal Series** — the new tab, and the Zoom button (click it; it should open your meeting).
- The nav on any other page, to see that seven items still wrap the way you want them to.

Then publish:

```sh
deploy/deploy.py                      # dry run: read the plan
deploy/deploy.py --upload             # publish
deploy/deploy.py                      # confirm: 0 new, 0 changed
```

### What to expect from the publish

**The first `--upload` sends the whole site, 33.4 MB, not just the changed pages.** The server has
no `.f3l-deploy-manifest.json` yet — Step 0's tooling has never had a live run — so the dry run
lists all 31 files as new: the 8 pages, `styles.css` and 22 files under `assets/`. Most of the
volume is photos (`wagon.jpg` 6.6 MB, `ABQPilots.PNG` 6.2 MB, three around 4 MB). Over plain FTP
that is minutes, not seconds. Let it finish — the manifest is written last, and a run that dies
partway leaves the old state and re-sends next time. Every later deploy sends only what changed.

The dry run also lists two **remote-only** files, `README.txt` and `assets/IMG_2381.PNG`, leftovers
of the old VS Code sync. They are left alone unless you pass `--delete`. Don't, unless you have
decided to remove them.

If it stops with exit 2 and a line about the password, the env file at
`~/.config/f3l-series-website/deploy.env` is not readable on the machine you are on;
`deploy/README.md` § First-time setup covers it. It is present and working on Bishop — the dry run
connected from here.

## How to respond

Leave your feedback as a comment on the task card
"[RC Sailplanes & Helis] [needs-you] Try the new functions yourself" **before** clearing its label —
clearing the label is what moves the step on, and reopening this session does not. If the publish
went through and the live site looks right, say so there and clear the label. If something needs
changing, say what, and leave the label in place.
