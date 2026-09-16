# Risks — Step 1: Schedule updates, CVRC Dec 5–6 event, and a Postal series tab

Step: https://trello.com/c/6cilqSP5   Written: 2026-09-15 by task 6aa97ff13c11f0740a124547
Design: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-design.md`

## What breaks while this change is in flight
(none)

## What could go wrong with this change
- **The Zoom placeholder goes live** · likelihood medium · impact medium · noticed by: the closing task's grep for `TODO(zoom-link)`; a "Zoom link coming soon" button on the live postal page · mitigation/rollback: closing task reports it; John supplies the link before `--upload`, or edits `postal.html`, commits and redeploys (one file).
- **A public Zoom link invites uninvited guests** · likelihood medium · impact low · noticed by: strangers in the Sept 27 meeting · mitigation/rollback: enable the waiting room or a passcode on John's Zoom meeting; the page can carry a "passcode in the RCGroups thread" note instead of the bare link if preferred.
- **The "Current Postal" card goes stale** · likelihood high · impact low · noticed by: the page naming the September F3L postal once October's F5L postal has opened · mitigation/rollback: the card's wording points at the RCGroups thread for the current month's dates and task, so a stale date is never the only answer; refreshing it is one line and a redeploy.
- **Wrong or swapped results links** · likelihood low · impact low · noticed by: clicking each 🏆 link in the preview shows a different event's standings · mitigation/rollback: event ids are tabulated in the design; fix the href and redeploy.
- **The PGMC 2026 card is kept when John meant "replace"** · likelihood medium · impact low · noticed by: John at review or on the live site · mitigation/rollback: delete one card, commit, redeploy.
- **Nav change misses a page** · likelihood low · impact low · noticed by: the preview sweep in the closing task (`grep -L postal.html *.html`) · mitigation/rollback: add the item, redeploy that page.
- **Publishing from a dirty or unreviewed worktree** · likelihood low · impact medium · noticed by: `deploy.py --upload` refuses a dirty tree; the server manifest records the commit · mitigation/rollback: commit first; redeploy from the intended commit with `--force` if needed.
- **First live deploy of Step 0 tooling coincides with this content** · likelihood medium · impact low · noticed by: the dry run lists every file as new (no manifest yet) · mitigation/rollback: expected on a first run; follow the acceptance checklist in `deploy/README.md`, then a second dry run shows nothing to send.
