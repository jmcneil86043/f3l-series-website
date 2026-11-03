# Output notes — Design the approach and write the implementation plan

Task: https://trello.com/c/ffsosn1p   Step: https://trello.com/c/aet0F8Yq   Date: 2026-10-15

## What was produced
- Spec: `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-spec.md` — no material open questions, so the design went ahead.
- Design: `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-design.md` — `deploy/deploy.py` as a gh-pages publisher built with git plumbing (blob-id diff against `origin/gh-pages`, HTTPS live check, one commit with audit trailers, same CLI), `deploy/verify.sh` for the plan's §11, footer `https://`, docs and tests, ledger supersessions, and the twelve-step cutover runbook for John's two existing gates.
- Risks: `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-risks.md`.
- Review hand-off: `migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/ffsosn1p-handoff.md`.
- Request snapshot: `migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/ffsosn1p-request.md`.
- Three implementation tasks plus the review and try items, requested via the sentinel's `checklist_items_to_add`; one `decisions` entry (the plumbing build and the retired manifest).

## Facts established while orienting
- This branch is cut from `main` at `9524fad`; local `main` is four commits behind `origin/main` (`b5ef709`: `deploy/backup.py`, two ledger lines). `origin/step/DJy1ViGr-select-web-hosting` (`0bcbe5f`) contains `origin/main` plus `select-web-hosting/` and the 2026-10-14/15 ledger lines. Neither is in this worktree; the design's task 1 merges the hosting branch in.
- GitHub: repo `jmcneil86043/f3l-series-website` is **private**, default branch `main`, no Pages site (`GET /pages` → 404), no `gh-pages` branch; `gh` 2.93.0 is authenticated as `jmcneil86043` (scopes gist, read:org, repo) and `ssh -T git@github.com` authenticates, both from Bishop.
- DNS (8.8.8.8): apex `A 65.254.248.183` TTL 14400; `www CNAME f3lcontestseries.org.` TTL 14400; MX `mxa/mxb.mailgun.org`; TXT `v=spf1 include:mailgun.org ~all`; `jmcneil86043.github.io` resolves to the four Pages addresses.
- Deploy set via `collect_deploy_set()`: 31 files, 35,018,920 bytes — matches the plan's inventory.
- Old host: `robots.txt` 200 (empty); `.f3l-deploy-manifest.json` present, last deploy 2026-09-21 by jam@Mika; the `.doc` serves as `application/msword`, 56,320 bytes; unknown User-Agents get 465 (needed a browser UA for these probes).
- `https://www.soarabq.org/` fails certificate verification (curl 60, name mismatch); `http://` is 200. The two soarabq links stay `http://`.
- Tools on Bishop: Python 3.14.7, git 2.54.0, `op` 2.40.0 (contradicting the 2026-09-15 ledger line; the closing task adds a line).
- Git plumbing probe from this worktree: `git hash-object -w --stdin-paths`, `git update-index --index-info` into a temporary `GIT_INDEX_FILE`, `git write-tree` — all work; the probe wrote three loose objects and no ref, and the working tree stayed clean.
- No running launcher job other than this one; no task in the plan touches task-dispatcher, trello-automation or any live MCP server, so the design has no Runner impact section.

## Sources read
- `decisions/F3L-Series-Web-Site-decisions.md` (this branch) and the same file on `origin/step/DJy1ViGr-select-web-hosting` via `git show`.
- `select-web-hosting/migration-plan.md` (hosting branch, via `git show`): §1, §2 (2.1–2.5), §3, §4.1, §4.2, §4.6, §5 (5.1–5.4), §7 (7.1–7.4), §10, §11, §12, §14, §15, §16. Skipped §6, §8, §9, §13 (Plan A, C, D and the cancellation — not this card).
- `select-web-hosting/comparison.md` (hosting branch): §2 (the Pages prohibited-uses note), §6, §8 GitHub Pages sources C1–C5, §9 runner-up section.
- `select-web-hosting/step-outputs/WfxlsOfV-handoff.md`, `R5S2o7dv-handoff.md`, `R5S2o7dv-output-notes.md` (hosting branch).
- `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md`.
- `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-spec.md`, `step-outputs/gqaNXa1D-output-notes.md`, `step-outputs/xa6BE0FD-handoff.md` (first 60 lines, for the hand-off shape).
- `deploy/deploy.py`, `deploy/README.md`, `deploy/preview.sh`, `deploy/deploy.env.example`, `deploy/tests/test_deploy.py` (header, fixtures and the test list), `README.txt`, `.gitignore`, `.claude/settings.json`, the eight pages (grep for `http://`).
- Skipped deliberately: `step-0-…/6PnyeVnB-spec.md` and `-risks.md`, `step-0-…/step-outputs/*` and `step-1-…/requirements/gqaNXa1D-design.md`, `-risks.md`, the other step-1 output notes — the Step 0 design covers the deploy tool this step rewrites, and Step 1 was content work with no bearing here. `select-web-hosting/requirements.md` — its R numbers are restated where they matter in the plan and comparison.

## Not done / for the reviewer
- Nothing was pushed, no GitHub setting or DNS record changed, no site file edited. The three loose git objects from the plumbing probe are unreferenced and harmless.
- The runner inserts the checklist items after this task's item; the card's existing gates (items 2 and 3) will follow them. If they land out of order, the design's checklist list is the intended order.
