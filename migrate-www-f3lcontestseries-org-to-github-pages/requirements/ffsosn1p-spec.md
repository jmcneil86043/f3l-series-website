# Spec — Migrate www.f3lcontestseries.org to GitHub Pages

Step: https://trello.com/c/aet0F8Yq   Written: 2026-10-15 by task 6ad111555be7e641a9577498
Derived from: the step card description (snapshot in `migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/ffsosn1p-request.md`); `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime as it stands on `origin/step/DJy1ViGr-select-web-hosting` (the 2026-10-14 and 2026-10-15 lines are not yet on `main`); `select-web-hosting/migration-plan.md` §2.5, §4.1–4.2, §4.6, §5, §7, §10–§12 and `select-web-hosting/comparison.md` §6, §8 (C1–C5), §9 on the same branch; `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md`; `deploy/deploy.py`, `deploy/README.md`, `deploy/tests/test_deploy.py` as checked out at 9524fad.

## What this step delivers
After this step, www.f3lcontestseries.org is served by GitHub Pages: every page and download loads over HTTPS with a valid certificate on both names, the bare name redirects to www, and nothing but the site itself is reachable there. Publishing works the way it does today — preview the checkout, run the deploy command and read its plan, then run it again with `--upload` — but the deploy is now a push to the repository, which has become public, and needs no host password. The old hosting account is left exactly as it is, still serving the site until DNS moves, and still available as the rollback until a later card cancels it.

## In scope
- `deploy/deploy.py` rewritten for Pages with today's command line, flags, exit codes and report headings; `deploy/tests/test_deploy.py`, `deploy/README.md`, `deploy/deploy.env.example` and the `README.txt` pointer follow.
- A scripted form of the migration plan's §11 verification list, usable before DNS moves (`--resolve`) and after.
- The `gh-pages` branch built from the deploy set, first published by a worker (plan §7.2 step 4).
- The §10 site-file cleanup: the footer self-link on all eight pages becomes `https://`.
- The ledger: the 2026-09-13/15 FTP deploy lines marked superseded, pointing forward.
- A runbook for the two `[needs-you]` gates already on the card: Pages setup, the §5.2 TTL schedule, the §7.3 cutover, the §11 checks, and §12 rollback values.

## Out of scope
- Anything on the old host: no file, `.htaccess`, billing or account change (plan §5.3 rule 5, §13 — a separate, later card).
- Deleting `deploy/backup.py` (after §13.1's final backup, not before).
- www.mcneilco.com, the SPF record, HSTS, a GitHub Action, a `robots.txt`, the Pages "private site" option.
- Merging the select-web-hosting step into `main` (its own gate; this branch carries its commits so either lands first).

## Success criteria
- From a plain client, all eight pages, `styles.css` and the bulletin `.doc` (served as `application/msword`) return 200 at `https://www.f3lcontestseries.org/`; `https://f3lcontestseries.org/` answers 301 to the www name; `http://` answers a redirect to `https://`; the certificate covers both names and is not the old `*.bizland.com` one; a missing path is a 404.
- `https://www.f3lcontestseries.org/decisions/`, `/deploy/`, `/README.txt` and every step folder are 404.
- The GitHub repository is public, Pages publishes the `gh-pages` branch with custom domain `www.f3lcontestseries.org` and Enforce HTTPS on; `main` is never the Pages source.
- `deploy/deploy.py` with no flags exits 0 and reports 0 new, 0 changed against `gh-pages`, and says the live site matches; after one page is edited and committed, `--upload` publishes that page only and the live site shows it within a few minutes.
- The §11 verification script passes against the public names, and the `f3lcontestseries.org` MX and TXT records are unchanged from before.
- The ledger's FTP lines read **superseded** with a pointer to the Pages line; `deploy/README.md` describes no FTP step.

## Constraints from the ledger
- "**2026-10-15 · www.f3lcontestseries.org moves to GitHub Pages from this repo, which becomes public; the site is published from a `gh-pages` branch built by `is_deploy_path()`, never from the root of `main`; the zone stays at Google Cloud DNS (four Pages A records at the apex, `www` CNAME to `jmcneil86043.github.io`, custom domain set to the www name); the shared FatCow/iPage/Network Solutions account is left behind.**" — `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime (on `origin/step/DJy1ViGr-select-web-hosting`).
- "**2026-10-14 · The F3L site leaves the shared iPage/Network Solutions account for its own static host with HTTPS, separate from mcneilco.com …** Step 2 (HTTPS on the current host) is superseded by this unless John says otherwise." — same section.
- "**2026-09-13 · `smartftp.json` … is gitignored and untracked; deploy credentials never live in the repo.**" — same section; still binding (there is no longer a deploy credential at all).
- "**2026-09-13 · The site deploy runs from Bishop (or John's Mac) as deploy/deploy.py invoked by hand or by a step worker … no GitHub Action is wired.**" — same section; the "from Bishop or John's Mac, by hand or by a worker, no Action" part carries over; the credentials clause is what this step supersedes.

## Assumptions
- The migration plan and the 2026-10-15 ledger lines are on `origin/step/DJy1ViGr-select-web-hosting`, not on `main`; this step's branch merges that branch in as its first act. Not material: the merge touches no site file, and the two steps land on `main` in either order.
- The two `http://www.soarabq.org/` links stay as they are: measured today, that host's HTTPS certificate is for another name, so an `https://` link would fail. Not material: two hrefs, revisited whenever they fix it.
- The server-side manifest (`.f3l-deploy-manifest.json`) is retired; the `gh-pages` commit history is the audit record. Not material: "what is live" is still one command, documented in the README.
- The first `gh-pages` push is done by a worker before John's gate, while the repo is still private (pushing a branch needs no Pages). Not material: nothing is served until John sets the source.
- The post-cutover TTL is 3600 s (plan D6, recommendation unchanged in §2.5). Not material: a number in the runbook John can change on the day.
- No `robots.txt` is added; the old host's empty one and Pages' 404 mean the same to crawlers. Not material: one empty file either way.
- Enforce HTTPS is switched on by John after Pages issues the certificate (plan §7.3 step 10), never by the script. Not material: a one-time setting.
- The pre-existing gates (card items 2 and 3) stay where they are, after the inserted items, so "Try the new functions yourself" runs before Pages is enabled; the hand-off says what can be tried at that point. Not material to the design.

## Open questions (what)
(none)
