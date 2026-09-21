# Design — Step 1: Schedule updates, CVRC Dec 5–6 event, and a Postal series tab

Step: https://trello.com/c/6cilqSP5   Written: 2026-09-15 by task 6aa97ff13c11f0740a124547
Spec: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-spec.md`
Ledger: `decisions/F3L-Series-Web-Site-decisions.md`

## Summary

Hand-edited static HTML, in the site's existing idiom (one `.content-card` per section, `.event-card` per contest, inline status lines, `styles.css` untouched except where noted). Two content changes and one new page:

1. `schedule.html` (and the mirrored list on `index.html`): four completed events with results links, CVRC added, PGMC 2027 added.
2. New `postal.html` + a "Postal Series" menu item on all eight pages.
3. Verify in `deploy/preview.sh`, dry-run `deploy/deploy.py`, commit. John publishes with `--upload` after his review.

The pull-string video is **not** embedded: its existing link on `howto.html` stays exactly as it is (John, 2026-09-15). No build step, no JavaScript beyond what the pages already have, no new CSS rules.

## Facts gathered (2026-09-15)

From F3XVault series 438 ("F3L Series of Contests 2026") and its event pages; the RCGroups threads are JavaScript-gated from this machine and could not be read except the CVRC thread's first post via a text proxy. **The postal thread's opening post was pasted in by John on 2026-09-15** and is the source for everything on `postal.html`.

| Event | Dates | F3XVault event_id | State |
|---|---|---|---|
| OG F3L, PMGC Gliderport, AZ | Mar 7–8 2026 | 4162 | completed, standings posted |
| 2026 F3L International, Balloon Fiesta Park, NM | Jun 13–14 2026 | 4338 | completed, standings posted |
| 2026 F3L National Championships, Muncie, IN | Jul 23–24 2026 | 4367 | completed, standings posted |
| 2026 F3L TPG Coastal Cooler, Encinitas, CA | Aug 29–30 2026 | 4157 | completed, standings posted |
| 2026 F3L CVRC Visalia, CA | Dec 5–6 2026 | 4516 | upcoming, registration open |

CVRC particulars (thread 4943121, first post): host Central Valley RC Soaring Club (https://cvrcsoaring.wordpress.com/), field at 8400 Ave. 320, Visalia (F3XVault calls it "CVRC Field at Russell Pond"); Friday Dec 4 field set-up and open flying 10am–4pm; CD Tim Johnson, assistant Mark Browning; entry $60; registration on F3XVault closes midnight Thu Dec 3; nine rounds, one drop after round 4; FAI-legal bungees (15 m rubber + 100 m line); lunch and water both days; described as the closing round of the 2026 series.

Video ZSMni8FZHJ4: title "Installing Spring Hinges and Pull Strings on a 2m RES Glider", channel TorreyPinesGulls. Already linked (bare `<a>`) in `howto.html` line 96 under "Setting Up Your F3L Sailplane" as "Pull-String Control Setup Guide" — that link is the delivery and is left untouched.

Postal particulars (thread 4942041, opening post by Ryan Woebkenberg and Ed LaCroix): run by the F3L Series Contest Series board; Ryan is CD and thread moderator, Ed contributes content and answers questions; contests in both F3L and F5L, alternating months; FAI rules except where noted, per-class rules attached to the opening post; each contest runs nine days — two weekends plus the week between — and the task may be flown on any day in that window; scoring by Gliderscore; entry by emailing a name to F3LF5LPostal@gmail.com (the thread obfuscates the address), registration carries forward to every later month automatically, and the same address removes you; bragging rights only, scores on the honour system; feedback invited. Calendar as given: **F3L, September 19–27 2026, 5 rounds**. F5L is confirmed as F3L with an electric launch instead of the bungee. The September postal closes on Sept 27, the day of the Zoom meeting.

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

## howto.html

No content change. The existing "Pull-String Control Setup Guide" link (line 96, → `https://www.youtube.com/watch?v=ZSMni8FZHJ4`) is the video's place on the site and stays as it is; an embedded player was considered and declined. The page's only edit is the Postal Series nav item, same as the other pages.

## postal.html — the new page

Copy the head/header/footer of `schedule.html`, title "Postal Series - F3L Contest Series", nav item active. Content comes from the postal thread's opening post (Ryan Woebkenberg and Ed LaCroix), supplied by John on 2026-09-15 — see § Facts. Body, top to bottom:

1. **Card "F3L and F5L Monthly Postal"** — what it is and how a round runs. Draft prose:

   > The F3L Contest Series board runs monthly postal contests for 2 m RES woody gliders, in both F3L and F5L. A postal is flown at your own field, on your own schedule: each contest opens for nine days — two weekends and the week between them — and you fly the assigned task on whichever of those days suits you. Scoring is done with Gliderscore, and FAI rules govern the planes and the flying except where the contest says otherwise. F5L is F3L with an electric launch in place of the bungee.
   >
   > The two classes alternate months, so a given month is either an F3L postal or an F5L one. Ryan Woebkenberg is the contest director and moderates the threads; Ed LaCroix contributes content and answers questions. You are flying for bragging rights — the contests work because everyone trusts everyone else to report scores honestly, and the point is to fly more, get better and have fun.

   Then a `.btn` → the thread (https://www.rcgroups.com/forums/showthread.php?4942041-F3L-and-F5L-Monthly-Postal), labelled "Postal thread on RCGroups", with a sentence noting that the class rules for each class are attached to the thread's opening post and that each month's dates and task are posted there. The thread stays the authority; the page does not restate the rules (spec § Out of scope).

2. **Card "Current Postal"** — an `.event-card` in the schedule page's idiom so the two pages look related:

   **September 19–27, 2026 · F3L Postal · 5 rounds**, with a line that the next postal is F5L and that dates and tasks are announced in the thread and by email to everyone registered.

   This card is the one part of the page that goes stale (see Risks); its wording points at the thread for the current month so a reader is never stranded on an old date.

3. **Card "How to Enter"** — short, because entry is one email:

   > Email your name to F3LF5LPostal@gmail.com and you are in. You only register once: after your first postal you are added to every following month automatically, and you will be told each month's dates and task by email. Email the same address any time to be taken off the list. Suggestions for improving the postals are welcome — these are new and the organisers are asking for feedback.

   The address is rendered as a `mailto:` link. The thread obfuscates it (`"F3LF5LPostal" "at" "gmail" "dot" "com"`) against scrapers; **see Open decisions** — if John would rather keep the organisers' obfuscation, the page shows the spelled-out form as plain text with no `mailto:`, which is a one-line change.

4. **Card "After-Postal Zoom Meeting"**: "Sunday, September 27, 2026 · 7:00 PM PDT (10:00 PM EDT)", "Hosted by John McNeil", and a line that this falls on the September postal's closing day — a chance to talk through how the month went, ask questions and hear what is next. `.btn` "Join the Zoom meeting" whose href is the link from the card comment. Until John supplies it, the href is `#` and the button text reads "Zoom link coming soon" with an HTML comment `<!-- TODO(zoom-link): paste the link from the step card comment -->`; the closing task must not publish with the placeholder in place (see Tasks).

5. **Card "Related"**: links to `schedule.html` and `results.html`, and the series thread already linked from the Stay Updated card, in `.resource-list` style.

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
| `postal.html` | new | Postal Series page |
| `results.html`, `about.html`, `host.html`, `highstart.html`, `howto.html` | edit | nav item only |
| `README.txt` | edit | add `postal.html` to the structure list |

`styles.css`, `assets/`, `deploy/` untouched.

## Implementation tasks

1. **Schedule and home page content** — `schedule.html`: rename Previous → Completed, four completed cards with F3XVault results links, Nationals date, CVRC card, PGMC Mar 6–7 2027 card; `index.html`: CVRC card. Check in the preview, commit. Size: 2 files, ~15 min.
2. **Postal page and navigation** — new `postal.html` per § postal.html (Zoom placeholder if the link is still missing from the card description); add the Postal Series nav item to all eight pages; `README.txt` structure line. Leave the pull-string link in `howto.html` alone. Check every page in the preview, commit. Size: 9 files, ~20 min.
3. **Closing: verify and dry-run** — run the deploy unit tests, `deploy/preview.sh` sweep of all pages (curl every page and every `href` between them for 200), `deploy/deploy.py` dry run and record its plan in the output notes, confirm no `TODO(zoom-link)` remains (if it does, say so in the output notes so the try item knows to fix it before `--upload`), commit. Size: 0–1 files, ~10 min.

Checklist names as they should appear on the step card, after this task's item:
1. `[needs-you] Review the design and plan`
2. `Update schedule.html and index.html: completed statuses with F3XVault results links, CVRC Dec 5–6 2026 card, PGMC Mar 6–7 2027 card`
3. `Add postal.html (Postal Series page with the Sept 27 Zoom announcement), the Postal Series nav item on every page, and the README.txt structure line`
4. `Closing: run deploy tests, preview sweep of every page, deploy dry run, confirm no Zoom placeholder remains, commit`
5. `[needs-you] Try the new functions yourself`

The try item is where John previews the worktree and runs `deploy/deploy.py --upload` (the card's "deploy once reviewed").

## Runner impact

(none — no task touches task-dispatcher, trello-automation or any MCP server; only site HTML and README.txt.)

## Open decisions

- **Zoom link source.** The link is in a comment on the step card, which workers on this machine cannot read. The cleanest fix is for John to paste it into the step card *description* (or reply with it in the review comment); task 2 then uses it directly instead of the placeholder.
- **PGMC "move".** Interpreted as add-a-2027-card and keep the completed 2026 card. If "move" meant replace, task 1 drops the 2026 OG F3L card instead.
- **Postal email address.** The page renders `F3LF5LPostal@gmail.com` as a `mailto:` link; the organisers deliberately obfuscated it in the thread. Say if you would rather the page match their obfuscation (plain text, no `mailto:`) — one line in task 2.
- **The "Current Postal" card.** Carries the September 19–27 F3L dates because they are live at publish. Say if you would rather the page name no dates at all and point only at the thread, which never goes stale.
- **Nationals date** changed to July 23–24 to match F3XVault; revert in task 1 if the site's 22–23 was right.
