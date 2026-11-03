# Hand-off: try the Pages publisher, then run the two cutover gates

## Goal

www.f3lcontestseries.org moves from the shared iPage/Network Solutions account to GitHub
Pages, published from the `gh-pages` branch of this (soon-public) repo, with the zone
staying at Google Cloud DNS. Everything the worker side owed is done and committed; what
remains is John's: try the new tools, make the repo public + configure Pages + lower the
TTLs, then merge, cutover the DNS and verify.

## Current status

- **Tests:** `python3 -m unittest discover -s deploy/tests` — 50 tests, OK.
- **First publish done:** `deploy/deploy.py --upload` created `origin/gh-pages` as commit
  `32859f04` (31 deploy-set files + `.nojekyll` + `CNAME` = 33 paths; verified by
  `git ls-tree -r` — no `decisions/`, `deploy/`, `README.txt` or step folder). A second
  dry run says 0 new / 0 changed and reads `Last deploy:` from the commit trailers.
- **Nothing is served yet, by design:** the repo is still private and no Pages source is
  configured, so Pages has nothing to build (a `--resolve` run right after the publish
  shows 404s on the content checks — status, not failure). The live site still resolves to
  the old iPage host, which is untouched and stays as the rollback.
- **Ledger updated:** the three FTP lines (2026-09-13 ×2, 2026-09-15) read
  **superseded 2026-10-15** pointing at the Pages line; a new line records `op` 2.40.0 on
  Bishop; the deploy-design line was already in the ledger (harvested from the design
  task's sentinel).
- **Branch:** the step branch is committed and pushed to origin; it is not merged — that
  is the last checklist item.

## What happened

This is the Closing task of the step. It ran the test suite, did the first
`deploy/deploy.py --upload` (creating `gh-pages` on origin while the repo is still
private — pushing a branch needs no Pages), checked the published tree and the commit
trailers, re-ran the dry run to confirm "nothing to do", made the ledger edits per the
design's Ledger section, and captured evidence. Full evidence (dry-run output, ls-tree,
the `--resolve` run, the MX/TXT pre-cutover baseline) is in
`migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/TrT2UGML-output-notes.md`.
The design's implementation plan is `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-design.md`;
the site-wide plan is `select-web-hosting/migration-plan.md` (§ numbers below are its).

## Files & paths

All relative to this worktree root.

- `deploy/deploy.py` — the Pages publisher (dry run / `--upload`; same CLI as the old
  FTP deploy). Read `deploy/README.md` first.
- `deploy/verify.sh` — the migration plan's §11 checks as a script (`--resolve` pre-DNS,
  `--base` for another URL).
- `deploy/README.md`, `deploy/deploy.env.example`, `README.txt` — rewritten for Pages.
- `deploy/tests/test_deploy.py` — 50 tests against a temp bare repo.
- `decisions/F3L-Series-Web-Site-decisions.md` — the superseded marks and the new lines.
- `migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/TrT2UGML-output-notes.md`
  — the evidence for this closing task.
- `select-web-hosting/migration-plan.md` — §5.2 (TTL schedule), §7 (Pages setup and
  cutover), §11 (verification), §12 (rollback).
- `deploy/backup.py` — old-FTP safety copy, deliberately untouched (dead until the
  §13.1 final backup; see the output notes' flag for the later old-host card).

## Pending checklist items

1. `[needs-you] Try the new functions yourself` — **this gate, now.**
2. `[needs-you] Make the repo public, set the Pages source to the gh-pages branch and
   the custom domain to www.f3lcontestseries.org, and lower the apex A and www CNAME TTLs
   to 300 at Google Cloud DNS` — gate 1 below.
3. `[needs-you] Merge the branch into main and push (steprunner-launcher merge-step on
   Bishop), then confirm the site is live on Pages with HTTPS on both names and the bare
   name redirecting to www` — gate 2 below, at least 48 h after gate 1's TTL drop.

## Open decisions

(none) — the design's open items (sibling-branch merge, live-check cost, `--force`
meaning) were settled when the design review passed; if trying the tools surfaces a
problem with any of them, say so in the response.

## The ask

**Try the new functions, then work the two gates in order.**

What you can try *now* (repo still private, Pages not yet configured):

- `deploy/deploy.py` — the dry run. Expect `Remote: origin/gh-pages @ 32859f0`, a
  `Last deploy:` line, 0 new / 0 changed / 31 unchanged, and `Live: not checked` (the
  name still points at the old host; that line becomes a real comparison after cutover).
  `--verbose` logs every git command and fetch.
- The publish loop: edit a page, commit, dry run shows the one Changed file,
  `--upload` publishes it, second dry run is 0/0. Note: every `--upload` leaves a
  publish commit on `gh-pages` — that is by design, the commit log is the audit trail, so
  a try-edit is fine (revert and re-publish when done if you like the tree back exactly).
  The site itself does **not** change from this — nothing is served until gate 1.
- `deploy/verify.sh --resolve 185.199.108.153` — shows the pre-DNS mode (checks 6-7
  skip, 8 reports the `*.github.io` cert for the eye). Content checks are 404 until you
  set the Pages source in gate 1; after that they should pass (gate 1, step 4).

**Gate 1** — repo public, Pages source, custom domain, TTL 300 (plan §7.2 steps 1-6, §5.2):

1. Make the repo public. UI: Settings → General → Danger Zone → Change visibility. Or:
   `gh repo edit jmcneil86043/f3l-series-website --visibility public --accept-visibility-change-consequences`.
   This publishes `decisions/` and the step folders as repository content (accepted,
   ledger 2026-10-15).
2. Settings → Pages → Build and deployment: Source "Deploy from a branch", branch
   `gh-pages`, folder `/ (root)`. Or:
   `gh api -X POST repos/jmcneil86043/f3l-series-website/pages -f 'source[branch]=gh-pages' -f 'source[path]=/'`.
3. Custom domain: `www.f3lcontestseries.org` (the www name, not the apex — that is what
   gives the apex→www 301). Or:
   `gh api -X PUT repos/jmcneil86043/f3l-series-website/pages -f cname=www.f3lcontestseries.org`.
   GitHub will show a DNS warning until cutover; expected. Do **not** tick Enforce HTTPS
   yet.
4. Pre-DNS gate: `deploy/verify.sh --resolve 185.199.108.153` passes checks 1-5 and 10-13
   (apex, http→https and certificate checks are public-run only). If Pages has not
   finished its first build, wait a minute and re-run.
5. Google Cloud DNS, zone `f3lcontestseries.org`: lower the TTL to **300** on exactly two
   records — the apex `A 65.254.248.183` and `www CNAME f3lcontestseries.org.` (both 14400
   today). Touch no MX, no TXT, no NS. This is T−48 h.
6. Confirm the zone has no other A/AAAA/CNAME for either name (plan C5 — stray records
   block certificate issuance).

**Gate 2** — at least 48 h after step 5 (plan §7.2 step 7 → §7.3):

7. `dig +noall +answer @8.8.8.8 www.f3lcontestseries.org` shows TTL ≤ 300. If not, wait.
8. Merge the step branch into `main` and push — `/steprunner-merge` (steprunner-launcher
   merge-step) from the clone on Bishop; no merge-step command pushes by itself, so push
   after the merge. Then, from the clone, `deploy/deploy.py` dry run must say 0 new /
   0 changed — the merge does not change the site, and if it did, `--upload` first.
9. T−0, in Cloud DNS: `www.f3lcontestseries.org` CNAME → `jmcneil86043.github.io.`
   (TTL 300). Verify with dig and `deploy/verify.sh` (public run, checks 1-5, 10-13).
   Then the apex: replace `A 65.254.248.183` with the four A records
   `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   (TTL 300). www before apex.
10. Settings → Pages: wait for "certificate … issued" (minutes to an hour), then tick
    **Enforce HTTPS**. Or poll
    `gh api repos/jmcneil86043/f3l-series-website/pages --jq .https_certificate.state`
    until `approved`, then
    `gh api -X PUT repos/jmcneil86043/f3l-series-website/pages -F https_enforced=true`.
11. `deploy/verify.sh` with no flags — every check, including the apex 301, http→https
    and the certificate (check 9 prints MX/TXT; diff against the pre-cutover baseline in
    the output notes: `MX 10 mxb.mailgun.org. 10 mxa.mailgun.org. | TXT "v=spf1 include:mailgun.org ~all"`).
    The eye checks: eight pages in a browser, the bulletin `.doc` downloads and opens in
    Word, both F3XVault iframes on Results render.
12. T+48 h: raise the two changed records to **3600** (plan D6). Done — the old host is
    still serving its untouched copy and stays as the rollback until a later card
    cancels it.

**Rollback** at any point after gate 2 step 9: put the two records back — apex
`A 65.254.248.183`, `www CNAME f3lcontestseries.org.` — and clear the custom domain in
Settings → Pages. Five minutes at TTL 300 (plan §12.2). Nothing on the old host was ever
changed, so nothing is restored.

## How to respond

- Feedback on the try-out goes as a comment on the "Try the new functions yourself" task
  card before its label is cleared.
- John clears the `🤖 needs you` label himself, one gate at a time — that is what moves
  the step. An assistant reading this never clears a label or checks a Tasks box, and
  reopening a worker session never moves a gate either.
- Gate 2's merge is the step's close-out: the step is finished only when the branch is
  merged into `main` **and pushed**, and the site is confirmed live (step 11).
