# Output notes — Closing: tests, preview sweep, deploy dry run, Zoom placeholder check

Task: https://trello.com/c/xa6BE0FD   Step: https://trello.com/c/6cilqSP5
Written: 2026-09-16 by task 6aaae7832494e9aa9b6f7f7f
Design: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-design.md` § Verification and publish

This task changed no site files. It verified what the two implementation tasks produced and
recorded the deploy plan. All four checks passed.

## 1. Deploy unit tests

```
python3 -m unittest discover -s deploy/tests
Ran 48 tests in 0.141s — OK
```

`deploy/` is untouched by this step, so this only confirms nothing regressed.

## 2. Preview sweep — every page, every local reference

`deploy/preview.sh 18091` over this worktree, then:

- **All 8 pages HTTP 200**: `about`, `highstart`, `host`, `howto`, `index`, `postal`, `results`,
  `schedule`.
- **30 distinct local `href`/`src` references across all 8 pages: all 200, 0 broken.** That is
  every inter-page link, `styles.css`, all 22 images, and the bulletin `.doc` download on
  "Host a Contest".
- **`href="postal.html"` appears exactly once in every one of the 8 pages** — the nav item is on
  every page, including `postal.html` itself (active).

## 3. External links — all 65 checked

Every `http(s)` URL in the site was fetched. **Every link this step added or changed resolves**:

| Link | Result |
|---|---|
| Zoom join link on `postal.html` | 200 |
| F3XVault results, events 4162 / 4338 / 4367 / 4157 | 200 each |
| F3XVault registration, event 4516 (CVRC) | 200 |
| `https://cvrcsoaring.wordpress.com/` (CVRC club) | 200 |
| CVRC thread 4943121, postal thread 4942041 | 202 |
| Pull-string video `watch?v=ZSMni8FZHJ4` on `howto.html` | 200 |

RCGroups answers bot fetches with 202; the pages are live. Four vendor/reference links return a
bot-block rather than a failure (403 medium.com, homedepot, lowes; 406 knots3d) and open fine in a
browser. **One genuinely dead link found: `https://www.armsoar.com/products/e-medina-2-2m-almost-ready-to-fly`
in `howto.html` → 404.** It is present at the step's merge-base `10fc645`, so it pre-dates this
step and was left alone (out of scope). Worth a follow-up card.

## 4. No Zoom placeholder remains — confirmed

`grep -rniE 'TODO\(zoom|zoom link coming|placeholder|href="#"|TBD|XXX'` over every `*.html` and
`styles.css` returns **nothing in any page**. The only hit anywhere is the pre-existing
`/* Image Placeholders */` CSS comment in `styles.css:313`, unrelated.

`postal.html` carries the real link from the step card description § Zoom, verbatim:

- href `https://us02web.zoom.us/j/87288189436?pwd=szxaEUcVwMRp5ikkyx1xMinJYUTFbb.1`
- "Sunday, September 27, 2026 · 7:00 PM PDT (10:00 PM EDT)", hosted by John McNeil
- Meeting ID 872 8818 9436 · Passcode 932925

(Sept 27 2026 is indeed a Sunday.) `schedule.html:120`'s "Details Coming Soon" is the designed
status of the March 2027 PGMC card, not a placeholder.

## 5. Deploy dry run

```
deploy/deploy.py            # exit 0, nothing sent
Local:  …/6cilqSP5 @ 8c1ecd575b34c8067fc7f78ad087ce82c565cf23
Remote: ftp://jmcneil@ftp.mcneilco.com/f3l_series
No .f3l-deploy-manifest.json on the server: every file counts as new.
Totals: 31 new, 0 changed, 0 unchanged, 2 remote-only; 33.4 MB to send
```

**The server has no manifest yet** — Step 0's first live run has not happened — so every file is
listed as new rather than just the eight pages this step touched. The design anticipated exactly
this. The 31 files are the 8 pages, `styles.css` and the 22 files under `assets/`, `postal.html`
among them at 5.2 KB.

Remote-only, listed and left alone (no `--delete` was passed and none should be): `README.txt` and
`assets/IMG_2381.PNG`, leftovers of the old VS Code sync.

**Consequence for the publish:** the first `deploy/deploy.py --upload` sends the whole 33.4 MB over
plain FTP, not just the changed pages — mostly the large photos (`wagon.jpg` 6.6 MB,
`ABQPilots.PNG` 6.2 MB, three ~4 MB JPEGs). Expect it to take minutes, not seconds. Every run after
it sends only what changed. This is Step 0's acceptance checklist item 4, arriving here.

## State at the end of this task

Working tree clean apart from this file and the hand-off, which this task commits. `--upload` will
not be blocked by a dirty tree (and these two files are not in the deploy set in any case). Nothing
is left for the closing task; what remains is John's `[needs-you]` preview and publish.
