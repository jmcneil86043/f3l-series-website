# Hand-off: Review the design and plan for Step 1 (schedule, CVRC, Postal page)

## Goal
Update the F3L Contest Series site: mark the four 2026 contests already flown as complete with results links, add the CVRC Visalia Dec 5–6 2026 event, add the PGMC Mar 6–7 2027 date, and add a "Postal Series" page and menu item that also announces the Sept 27 Zoom meeting. Publish with the Step 0 deploy once reviewed.

## Current status
Spec, design and risks are written and committed on the step branch. No site file has been changed yet. The step is waiting on this review.

## What happened
- Read the site (all seven pages, `styles.css`, `README.txt`), the Step 0 design and output notes, and the decisions ledger.
- Gathered the facts from F3XVault: series 438 lists OG F3L (Mar 7–8), International (Jun 13–14), Nationals (Jul 23–24), Coastal Cooler (Aug 29–30) as completed with standings posted, and CVRC Visalia (Dec 5–6, event 4516) as upcoming with registration open. The CVRC thread's first post was read through a text proxy (host CVRC, field at 8400 Ave. 320 Visalia, Friday Dec 4 practice, CD Tim Johnson, $60, registration closes Dec 3, nine rounds).
- Could not read the postal thread or the series thread: RCGroups is JavaScript-gated from this machine (and the tollbit mirror returns 402). The postal page prose is therefore generic and yours to correct.
- The Zoom link is in a comment on the step card, which this machine cannot see; the design uses a marked placeholder until you supply it.
- Found that the video is already linked as a bare link on the How To page under "Setting Up Your F3L Sailplane"; John asked for that link to stay as it is, so no embed is added and `howto.html` gets only the nav item.
- Wrote the spec (no material open questions), the design, the risks doc, and this hand-off.

## Files & paths
- Spec: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-spec.md`
- Design: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-design.md`
- Risks: `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-risks.md`
- Request as received: `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/gqaNXa1D-request.md`
- Output notes: `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/gqaNXa1D-output-notes.md`
- Files the plan will touch: `schedule.html`, `index.html`, `howto.html`, new `postal.html`, nav in `results.html`, `about.html`, `host.html`, `highstart.html`, and `README.txt`.

## Pending checklist items
1. `[needs-you] Review the design and plan` (this gate)
2. `Update schedule.html and index.html: completed statuses with F3XVault results links, CVRC Dec 5–6 2026 card, PGMC Mar 6–7 2027 card`
3. `Add postal.html (Postal Series page with the Sept 27 Zoom announcement), the Postal Series nav item on every page, and the README.txt structure line`
4. `Closing: run deploy tests, preview sweep of every page, deploy dry run, confirm no Zoom placeholder remains, commit`
5. `[needs-you] Try the new functions yourself` (preview the worktree, then `deploy/deploy.py --upload`)

## Open decisions
From the spec's open questions: (none).

From the design's `## Open decisions`:
- **Zoom link source.** Workers cannot read card comments. Paste the Zoom link into the step card description (or into your review comment) so task 2 can use it instead of the placeholder.
- **PGMC "move".** Interpreted as add a Mar 6–7 2027 card and keep the completed Mar 2026 OG F3L card. Say if "move" meant replace.
- **Postal email address.** The page makes `F3LF5LPostal@gmail.com` a `mailto:` link; the organisers obfuscated it in the thread against scrapers. Say if you want the page to match their obfuscation instead.
- **The "Current Postal" card.** It names the September 19-27 F3L dates, which go stale in October. Say if you would rather the page name no dates and point only at the thread.
- **Nationals date.** Changed to July 23–24 to match F3XVault and the home page; say if 22–23 was right.

Risks in brief (full list in the risks doc): the Zoom placeholder could go live if the link never arrives (the closing task checks for it); a public Zoom link invites strangers (use a waiting room or passcode); a wrong results href or a missed nav item is caught in the preview sweep; the first live deploy may show every file as new if Step 0's first run has not happened yet.

## The ask
Review the design and plan. Approve as is, or answer the open decisions above (at minimum, supply the Zoom link).

## How to respond
Add your feedback as a comment on the task card for this gate, then clear its label. Clearing the label is what moves the step; reopening this session does nothing. If everything is fine, a comment saying "approved" plus the Zoom link is enough.
