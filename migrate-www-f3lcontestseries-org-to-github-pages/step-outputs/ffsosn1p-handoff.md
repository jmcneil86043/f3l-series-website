# Hand-off: review the design and plan for the GitHub Pages migration

## Goal

The step moves www.f3lcontestseries.org from the shared iPage/Network Solutions account to GitHub
Pages, per the 2026-10-15 ledger line and the migration plan's Plan B (§7). This task wrote the
spec, the design and the risks doc, and asked for the implementation items on the step card. The
next item is yours: read the design and say whether the workers may build it.

## Current status

Spec, design and risks are written and committed on this branch. Nothing else has changed: no site
file, no deploy code, no DNS record, no GitHub setting. The repo is still private, there is no
`gh-pages` branch, and the old host is untouched.

One thing to know before reading: the migration plan, the comparison and the 2026-10-14/15
ledger lines are **not on `main`** — they are on `origin/step/DJy1ViGr-select-web-hosting`, whose
merge gate (its last checklist item) has not been cleared. This worktree was cut from a `main`
that predates them. The design's first implementation task merges that branch into this one so
this branch carries the plan it cites and can edit the ledger lines it must supersede.

## What happened

Read the card, the ledger (both versions), the migration plan (§2.5, §4, §5, §7, §10–§12, §14–§16),
the comparison (§6, §8, §9), the Step 0 design, today's `deploy/deploy.py`, its tests and README,
and the hosting step's hand-offs. Checked the live state: repo private, no Pages site, `gh` and
ssh both authenticated to GitHub as `jmcneil86043` from Bishop, DNS unchanged (apex A
65.254.248.183 and `www` CNAME at TTL 14400, Mailgun MX and SPF present), deploy set 31 files /
35,018,920 bytes as the plan says, `www.soarabq.org` has no valid HTTPS, and the git plumbing the
design relies on works from a worktree (probed with a temporary index, nothing written to any ref).

The design in one paragraph: `deploy/deploy.py` keeps its command line and becomes a `gh-pages`
publisher — it hashes the deploy set with git, diffs blob ids against `origin/gh-pages`, fetches
the live site over HTTPS and compares, prints the same four headings, and with `--upload` writes
the tree (plus `.nojekyll` and `CNAME`) into a temporary index, commits it on top of the branch
with audit trailers and pushes. No credential; the server manifest is retired in favour of the
branch's history. A new `deploy/verify.sh` runs the plan's §11 checks, with `--resolve` for the
pre-DNS run. Footer links go `https://`, docs and tests follow, the ledger marks the FTP lines
superseded. Your two existing gates get a twelve-step runbook (Pages setup, TTL 300, 48-hour wait,
merge, cutover www-then-apex, Enforce HTTPS after the certificate, verify, TTL 3600) with the
rollback values.

## Files & paths

All paths relative to this worktree.

| Path | What |
|---|---|
| `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-spec.md` | spec — what the step delivers, success criteria, assumptions |
| `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-design.md` | design — the script, verify.sh, tests, docs, ledger, the cutover runbook, the three tasks |
| `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-risks.md` | risks |
| `migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/ffsosn1p-request.md` | the card as this task saw it |
| `migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/ffsosn1p-output-notes.md` | what was read and measured |
| `deploy/deploy.py`, `deploy/tests/test_deploy.py`, `deploy/README.md` | today's FTP deploy, to be rewritten |
| `decisions/F3L-Series-Web-Site-decisions.md` | ledger (this branch's copy lacks the 2026-10-14/15 lines until task 1 merges) |
| `select-web-hosting/migration-plan.md` | the plan — read it with `git show origin/step/DJy1ViGr-select-web-hosting:select-web-hosting/migration-plan.md` until task 1 merges |

## Pending checklist items

After this review, in the order requested from the runner:

1. Merge `origin/step/DJy1ViGr-select-web-hosting` into this branch; rewrite `deploy/deploy.py` as the gh-pages publisher and rewrite its tests (~30 min, the big one).
2. Add `deploy/verify.sh`; footer links to `https://`; rewrite `deploy/README.md` and `deploy/deploy.env.example`; `README.txt` line (~20 min).
3. Closing: tests, first `deploy/deploy.py --upload` (creates `gh-pages`), check its tree, ledger lines, output notes and the cutover hand-off, commit (~15 min).
4. `[needs-you] Try the new functions yourself` — dry run and `--upload` work at that point; the site is not served until the next gate.
5. (existing) `[needs-you] Make the repo public, set the Pages source to gh-pages and the custom domain, lower the two TTLs to 300` — runbook steps 1–6.
6. (existing) `[needs-you] Merge the branch into main and push, then confirm the site is live` — runbook steps 7–12, at least 48 h after item 5.

## Open decisions

From the spec: no material open questions. The assumptions taken are listed in the spec; the ones
worth a glance: the hosting branch is merged into this one first; the soarabq links stay `http://`
(their HTTPS is broken); the server manifest is retired; the worker does the first `gh-pages` push
while the repo is still private; TTL settles at 3600 afterwards; no `robots.txt`.

From the design's `## Open decisions`:

- **Merging a sibling step branch into this one** is the design's call. If you would rather merge
  the hosting step to `main` first, say so and task 1 does `git merge origin/main` instead.
- **Live check cost** — a full 35 MB fetch on every dry run, for one honest code path. The cheaper
  HEAD-per-asset variant is named if that is too slow.
- **`--force` meaning** — "publish a new commit even when nothing differs, so Pages rebuilds".
- **"Try the new functions yourself" runs before the Pages gate**; the closing hand-off will say
  what can be tried then.

## Risks summary

From the risks doc: making the repo public exposes the ledger, step folders and every stale branch
(accepted; task 3 re-checks history for the password first — delete unwanted branches before
flipping); a wrong Pages source would serve the ledger (verify check 13 catches it); a hand push
could drop `CNAME` (the script always writes it); the live check is slow or noisy pre-cutover (it
never changes the exit code); a cutover before the certificate issues shows a warning for up to an
hour (wait, then Enforce HTTPS); editing the zone risks touching MX/TXT (don't open them; before/
after diff in verify); a worktree `--upload` can publish what `main` lacks (dry run from the clone
after merge); the stale FTP `deploy.env` on Bishop still holds a password (delete it).

## The ask

**Review the design and plan.** Say yes, or say what to change, in a comment on the task card. The
specific things to confirm or overrule: the sibling-branch merge in task 1, the full-fetch live
check, the `--force` meaning, and the runbook's TTL 3600 at the end.

## How to respond

Feedback goes as a comment on the task card (https://trello.com/c/ffsosn1p) before its label is
cleared. **You clearing the `🤖 needs you` label yourself is what moves the step** — reopening this
session does not, and an assistant reading this hand-off never clears a label or checks a Tasks
box.
