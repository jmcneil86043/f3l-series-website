# Design — Step 1: Schedule updates, CVRC Dec 5–6 event, pull-string video, and a Postal series tab

Step: https://trello.com/c/6cilqSP5   Written: 2026-09-15 by task 6aa97ff13c11f0740a124547
Spec: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-spec.md`
Ledger: `decisions/F3L-Series-Web-Site-decisions.md`

## Summary

Hand-edited static HTML, in the site's existing idiom (one `.content-card` per section, `.event-card` per contest, inline status lines, `styles.css` untouched except where noted). Three content changes and one new page:

1. `schedule.html` (and the mirrored list on `index.html`): four completed events with results links, CVRC added, PGMC 2027 added.
2. `howto.html`: the pull-string video embedded where it is already linked.
3. New `postal.html` + a "Postal Series" menu item on all eight pages.
4. Verify in `deploy/preview.sh`, dry-run `deploy/deploy.py`, commit. John publishes with `--upload` after his review.

No build step, no JavaScript beyond what the pages already have, no new CSS rules (the stylesheet already defines `.video-container`, unused until now).

## Facts gathered (2026-09-15)

From F3XVault series 438 ("F3L Series of Contests 2026") and its event pages; the RCGroups threads are JavaScript-gated from this machine and could not be read except the CVRC thread's first post via a text proxy.

| Event | Dates | F3XVault event_id | State |
|---|---|---|---|
| OG F3L, PMGC Gliderport, AZ | Mar 7–8 2026 | 4162 | completed, standings posted |
| 2026 F3L International, Balloon Fiesta Park, NM | Jun 13–14 2026 | 4338 | completed, standings posted |
| 2026 F3L National Championships, Muncie, IN | Jul 23–24 2026 | 4367 | completed, standings posted |
| 2026 F3L TPG Coastal Cooler, Encinitas, CA | Aug 29–30 2026 | 4157 | completed, standings posted |
| 2026 F3L CVRC Visalia, CA | Dec 5–6 2026 | 4516 | upcoming, registration open |

CVRC particulars (thread 4943121, first post): host Central Valley RC Soaring Club (https://cvrcsoaring.wordpress.com/), field at 8400 Ave. 320, Visalia (F3XVault calls it "CVRC Field at Russell Pond"); Friday Dec 4 field set-up and open flying 10am–4pm; CD Tim Johnson, assistant Mark Browning; entry $60; registration on F3XVault closes midnight Thu Dec 3; nine rounds, one drop after round 4; FAI-legal bungees (15 m rubber + 100 m line); lunch and water both days; described as the closing round of the 2026 series.

Video ZSMni8FZHJ4: title "Installing Spring Hinges and Pull Strings on a 2m RES Glider", channel TorreyPinesGulls. Already linked (bare `<a>`) in `howto.html` under "Setting Up Your F3L Sailplane" as "Pull-String Control Setup Guide".

Existing site: 7 pages share an identical `<nav>` block (Home, Schedule, Results, About F3L, How To, Host a Contest). Nav links are relative; the deploy set is every top-level `*.html`, so a new page is published automatically.

## schedule.html

Keep the page structure (intro card → events → photo → registration info → stay updated). Changes inside the events card:

- Heading stays "2026 Contest Schedule". The intro sentence is kept.
- **"Completed Events"** (rename from "Previous Events"), four cards in date order: OG F3L, International, Nationals, Coastal Cooler. Each keeps its date, title, location, club link and blurb; the status paragraph becomes:
  `Status: Complete` · `🏆 Results on F3XVault` (href `https://www.f3xvault.com/?action=event&function=event_view&event_id=<id>`) · existing `📋 Contest Thread on RCGroups` link kept. The International card drops its `📝 Register on F3XVault` line (it becomes the results link). Nationals date becomes July 23-24, 2026 to match F3XVault and the home page.
- **"Upcoming Events"**, two cards:
  - **December 5-6, 2026 · CVRC F3L** · 📍 Visalia, California · club link "Central Valley RC Soaring Club" → https://cvrcsoaring.wordpress.com/ · blurb: closing round of the 2026 series at the CVRC field; Friday Dec 4 practice, open flying 10–4; nine rounds; entry $60; registration closes Dec 3. · `Status: Registration is Open` · 📋 thread (https://www.rcgroups.com/forums/showthread.php?4943121-2026-CVRC-F3L-Visalia-CA-Dec-5th-6th) · 📝 Register on F3XVault (event 4516).
  - **March 6-7, 2027 · Original Glider F3L** · 📍 Maricopa, AZ · Phoenix Model Glider Club link (existing) · blurb: the 2027 season opener. · `Status: Details Coming Soon` (the site's existing wording). No thread link: none known.
- Status colour and markup follow the existing inline style (`<span style="color: #2b7de9;">`), so nothing new in CSS.

## index.html

The "2026 F3L Series Contests" list gains a fifth card for CVRC (date, title, location, club link) after Coastal Cooler, in the same minimal format as its neighbours. The 2027 PGMC entry is not added to the home page (the list is titled 2026); it lives on the schedule.

## howto.html — the video

In the "Setting Up Your F3L Sailplane" card, replace the bare link list item with:

```html
<div class="video-container">
  <iframe src="https://www.youtube.com/embed/ZSMni8FZHJ4"
          title="Installing Spring Hinges and Pull Strings on a 2m RES Glider"
          allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
<p class="image-caption">John McNeil: installing spring hinges and pull strings on a 2m RES glider</p>
```

plus a plain link under it ("Watch on YouTube" → https://youtu.be/ZSMni8FZHJ4) for readers whose browsers block embeds. The `.video-container` and `.video-container iframe` rules already exist in `styles.css` (responsive 16:9). The card's lead sentence is reworded to name the video. The "F3L High-start Construction" card above it is unchanged; if the reviewer wants the video referenced there too, it is one `<li>`.

## postal.html — the new page

Copy the head/header/footer of `schedule.html`, title "Postal Series - F3L Contest Series", nav item active. Body, top to bottom:

1. **Card "F3L and F5L Monthly Postal"**. Two short paragraphs: what a postal is (each pilot flies the month's task at their own field and reports scores; F3L is bungee-launched, F5L the electric-launch sibling), and that the RCGroups thread carries the monthly task, the rules and the results. Button `.btn` → the thread (https://www.rcgroups.com/forums/showthread.php?4942041-F3L-and-F5L-Monthly-Postal). The prose is deliberately generic because the thread could not be read from here; John corrects it at review.
2. **Card "After-Postal Zoom Meeting"**: "Sunday, September 27, 2026 · 7:00 PM PDT (10:00 PM EDT)", "Hosted by John McNeil", one line on purpose (talk through the month's postal, questions, what's next), and a `.btn` "Join the Zoom meeting" whose href is the link from the card comment. Until John supplies it, the href is `#` and the button text reads "Zoom link coming soon" with an HTML comment `<!-- TODO(zoom-link): paste the link from the step card comment -->`; the closing task must not publish with the placeholder in place (see Tasks).
3. **Card "Related"**: links to `schedule.html` and `results.html`, and the series thread already linked from the Stay Updated card, in `.resource-list` style.

No image on this page (nothing suitable in `assets/`; a photo can be added later).

## Navigation (all pages)

Insert `<li><a href="postal.html">Postal Series</a></li>` after the Results item in `index.html`, `schedule.html`, `results.html`, `about.html`, `howto.html`, `host.html`, `highstart.html` and the new `postal.html` (active there). Seven items wrap fine at 768 px and stack at 480 px under the existing rules; no CSS change. Also add `postal.html` to the structure listing in `README.txt`.

## Verification and publish

- `deploy/preview.sh 18089` and fetch every page + `postal.html` (HTTP 200), open the schedule and postal pages in a browser through the SSH forward per `deploy/README.md`.
- `python3 -m unittest discover -s deploy/tests` (unchanged tooling; confirms nothing regressed).
- `deploy/deploy.py` dry run: expected plan is 8 pages **changed/new** (`postal.html` new, the seven edited pages changed), `styles.css` and `assets/` unchanged. If the server has no manifest yet (Step 0's first live run has not happened), every file shows as new; that is fine and is noted in the output notes.
- Publish: John runs `deploy/deploy.py --upload` from this worktree in the final `[needs-you]` item, after reviewing the preview and after the Zoom link is in place. A worker may run it instead if John says so in the review comment.

## Files

| Path | Status | Change |
|---|---|---|
| `schedule.html` | edit | completed statuses + results links, CVRC card, PGMC 2027 card, nav item |
| `index.html` | edit | CVRC card in the home list, nav item |
| `howto.html` | edit | video embed in the Setup card, nav item |
| `postal.html` | new | Postal Series page |
| `results.html`, `about.html`, `host.html`, `highstart.html` | edit | nav item only |
| `README.txt` | edit | add `postal.html` to the structure list |

`styles.css`, `assets/`, `deploy/` untouched.

## Implementation tasks

1. **Schedule and home page content** — `schedule.html`: rename Previous → Completed, four completed cards with F3XVault results links, Nationals date, CVRC card, PGMC Mar 6–7 2027 card; `index.html`: CVRC card. Check in the preview, commit. Size: 2 files, ~15 min.
2. **Postal page, navigation and video** — new `postal.html` per § postal.html (Zoom placeholder if the link is still missing from the card description); add the Postal Series nav item to all eight pages; embed the video in `howto.html`; `README.txt` structure line. Check every page in the preview, commit. Size: 9 files, ~20 min.
3. **Closing: verify and dry-run** — run the deploy unit tests, `deploy/preview.sh` sweep of all pages (curl every page and every `href` between them for 200), `deploy/deploy.py` dry run and record its plan in the output notes, confirm no `TODO(zoom-link)` remains (if it does, say so in the output notes so the try item knows to fix it before `--upload`), commit. Size: 0–1 files, ~10 min.

Checklist names as they should appear on the step card, after this task's item:
1. `[needs-you] Review the design and plan`
2. `Update schedule.html and index.html: completed statuses with F3XVault results links, CVRC Dec 5–6 2026 card, PGMC Mar 6–7 2027 card`
3. `Add postal.html (Postal Series page with the Sept 27 Zoom announcement), the Postal Series nav item on every page, the pull-string video embed in howto.html, and the README.txt structure line`
4. `Closing: run deploy tests, preview sweep of every page, deploy dry run, confirm no Zoom placeholder remains, commit`
5. `[needs-you] Try the new functions yourself`

The try item is where John previews the worktree and runs `deploy/deploy.py --upload` (the card's "deploy once reviewed").

## Runner impact

(none — no task touches task-dispatcher, trello-automation or any MCP server; only site HTML and README.txt.)

## Open decisions

- **Zoom link source.** The link is in a comment on the step card, which workers on this machine cannot read. The cleanest fix is for John to paste it into the step card *description* (or reply with it in the review comment); task 2 then uses it directly instead of the placeholder.
- **Video placement.** Embedded in the How To "Setting Up Your F3L Sailplane" card, where it is already linked and where the tow hook / launch bullet lives. If John meant the high-start construction card or `highstart.html`, say so in the review; it is a copy of one block.
- **PGMC "move".** Interpreted as add-a-2027-card and keep the completed 2026 card. If "move" meant replace, task 1 drops the 2026 OG F3L card instead.
- **Postal prose.** Generic wording, since the thread is unreadable from here. John can supply a paragraph (or the thread's opening post) in the review comment and task 2 will use it verbatim.
- **Nationals date** changed to July 23–24 to match F3XVault; revert in task 1 if the site's 22–23 was right.
