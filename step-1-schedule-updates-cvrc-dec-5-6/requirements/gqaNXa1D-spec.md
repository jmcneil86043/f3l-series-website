# Spec — Step 1: Schedule updates, CVRC Dec 5–6 event, pull-string video, and a Postal series tab

Step: https://trello.com/c/6cilqSP5   Written: 2026-09-15 by task 6aa97ff13c11f0740a124547
Derived from: the step card description (snapshot in `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/gqaNXa1D-request.md`); `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime; `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md` (deploy set, dirty-tree guard, preview); the F3XVault series page (series_id 438) and event pages 4162, 4338, 4367, 4157, 4516; the site as checked out at 10fc645.

## What this step delivers
After this step, a visitor to www.f3lcontestseries.org sees a schedule that matches the season as it stands: the four contests already flown are marked complete with a link to their results, the December CVRC contest in Visalia is listed with its registration link, and the next Phoenix contest shows its March 2027 date. A new "Postal Series" tab in the site menu describes the F3L and F5L Monthly Postal, links to its RCGroups thread, and announces the September 27 Zoom meeting with its join link. John's pull-string video is watchable on the page where launching is discussed. The changes are published with the Step 0 deploy after John has looked at them.

## In scope
- Schedule page: CVRC event card; completed status and results links for the four 2026 contests already held; the PGMC Mar 6–7 2027 entry.
- Home page: the mirrored contest list gains the CVRC event so the two lists agree.
- The pull-string video, embedded on the How To page where launching is discussed.
- A new Postal Series page, and its entry in the navigation of every page.
- Verifying in the local preview, a deploy dry run, and the live publish once reviewed.

## Out of scope
- Any change to the deploy tooling, the stylesheet's design language, or page layouts beyond the new page.
- A results page rewrite; results stay on F3XVault and are linked, not copied.
- Writing or restating the postal's rules from scratch; the thread stays the authority.
- The 2027 season schedule beyond the single PGMC date the card gives.

## Success criteria
- On the live site, the schedule shows OG F3L (Mar), International (Jun), Nationals (Jul) and Coastal Cooler (Aug) as complete, each with a working results link, and CVRC Dec 5–6 2026 and PGMC Mar 6–7 2027 as upcoming.
- Every page's menu has a "Postal Series" item that opens a page linking the postal thread and stating the Zoom meeting date, time in both zones, host, and join link.
- The video plays from the How To page.
- `deploy/deploy.py` dry run after the publish reports nothing to send, and the manifest on the server records the step's final commit.

## Constraints from the ledger
- "The site deploy runs from Bishop (or John's Mac) as deploy/deploy.py invoked by hand or by a step worker, with credentials in the environment or ~/.config/f3l-series-website/deploy.env; no GitHub Action is wired." — `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime, 2026-09-15.
- "`smartftp.json` … is gitignored and untracked; deploy credentials never live in the repo." — same section, 2026-09-13.

## Assumptions
- "Move the PGMC event to Mar 6–7 2027" means the next Phoenix contest is added as an upcoming 2027 entry, while the March 2026 OG F3L stays listed as complete (F3XVault shows it flown, results posted). Not material: it is one event card either way, and the reviewer can delete the 2026 card if "move" meant replace.
- The results link for each completed event is its F3XVault event page (event_view), which shows the standings directly; no separate results URL exists. Not material: one href per card.
- The Nationals were flown July 23–24 (F3XVault and the home page agree; the schedule page says 22–23). The schedule adopts 23–24. Not material: a date string.
- The postal page's description stays short and generic (a monthly contest flown at your own field, scores gathered in the RCGroups thread), because the thread is JavaScript-gated from this machine and could not be read. Not material: prose John can edit in the review; page structure is unchanged.
- The Zoom link is not in the card snapshot; the page carries a clearly marked placeholder until John supplies it (asked for in the review hand-off). Not material: one href.
- The video is already linked as a bare link in the How To page's "Setting Up Your F3L Sailplane" card, which also covers tow hook and launch; that card gets the embedded player. Its title is "Installing Spring Hinges and Pull Strings on a 2m RES Glider" (a setup topic), so it is not put inside Ed LaCroix's high-start article. Not material: placement of one embed, easy to move.
- The new page is `postal.html` with menu label "Postal Series", placed after "Results". Not material: name and position are one-line edits.
- The live publish is done by John in the final "Try the new functions yourself" item after he has previewed, because the card says "once the changes are reviewed". Not material to the content design.

## Open questions (what)
(none)
