# Output notes — Design the approach and write the implementation plan

Task: https://trello.com/c/gqaNXa1D   Step: https://trello.com/c/6cilqSP5   Date: 2026-09-15

## What was produced
- Spec: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-spec.md` — no material open questions, so the design went ahead.
- Design: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-design.md` — hand-edited HTML in the site's existing idiom: schedule/home updates, video embed on How To (the `.video-container` CSS already exists), new `postal.html` with a "Postal Series" nav item on all eight pages, preview + dry run, John publishes in the try item.
- Risks: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-risks.md`.
- Review hand-off: `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/gqaNXa1D-handoff.md`.
- Three implementation tasks plus the review and try items, requested via the sentinel's `checklist_items_to_add`.

## Facts established while orienting
- F3XVault series 438: OG F3L (4162), International (4338), Nationals (4367, Jul 23–24), Coastal Cooler (4157) completed with standings; CVRC Visalia (4516) Dec 5–6, registration open. Event pages show standings directly, so they serve as the results links.
- CVRC thread first post (via text proxy): Central Valley RC Soaring Club, field 8400 Ave. 320 Visalia, Friday Dec 4 practice 10–4, CD Tim Johnson (asst Mark Browning), $60, registration closes midnight Thu Dec 3, nine rounds with one drop after round 4, FAI-legal bungees, lunch and water both days.
- Video ZSMni8FZHJ4 is "Installing Spring Hinges and Pull Strings on a 2m RES Glider" (TorreyPinesGulls channel) and is already a bare link on `howto.html`.
- The site's schedule page says Nationals July 22–23; F3XVault and `index.html` say 23–24.
- `~/.config/f3l-series-website/deploy.env` exists on this machine, so a worker here can run the dry run; deploy tests pass (48 OK).
- RCGroups threads (postal, series, and the CVRC thread via WebFetch) are JavaScript-gated; the tollbit mirror returns 402. `.claude/settings.json` already allowlists those domains from an earlier attempt.

## Sources read
- `schedule.html`, `index.html`, `results.html`, `howto.html`, `highstart.html`, `about.html` (launch parts), `host.html` (nav), `styles.css`, `README.txt`, `.gitignore`, `.claude/settings.json`
- `decisions/F3L-Series-Web-Site-decisions.md`
- `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md`, `6PnyeVnB-spec.md`, `6PnyeVnB-risks.md`
- `step-0-design-and-implement-an-ftp-deployment/step-outputs/6PnyeVnB-output-notes.md`, `F6QxhKE1-output-notes.md`, `LLTDPUqU-output-notes.md`, `6PnyeVnB-request.md`
- `deploy/README.md`, `deploy/deploy.py` (grep for the deploy-set and manifest rules only)
- External: F3XVault series 438 and events 4162, 4338, 4367, 4157, 4516; CVRC thread 4943121 (text proxy); YouTube oEmbed for ZSMni8FZHJ4; https://cvrcsoaring.wordpress.com/
- Skipped: `step-0-…/step-outputs/F6QxhKE1-request.md` and `LLTDPUqU-request.md` (the output notes for those tasks cover them); `deploy/tests/test_deploy.py` and `deploy/preview.sh` (tooling this step does not change).

## Not done / for the reviewer
- The Zoom link and the postal thread text are inputs only John can supply; see the hand-off's open decisions.
- The runner inserts the checklist items after this task's item; if they land out of order, the design's Open decisions should be read with that in mind.
