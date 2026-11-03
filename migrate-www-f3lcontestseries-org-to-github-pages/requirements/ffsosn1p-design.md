# Design — Migrate www.f3lcontestseries.org to GitHub Pages

Step: https://trello.com/c/aet0F8Yq   Written: 2026-10-15 by task 6ad111555be7e641a9577498
Spec: `migrate-www-f3lcontestseries-org-to-github-pages/requirements/ffsosn1p-spec.md`
Plan: `select-web-hosting/migration-plan.md` (§ numbers below are its sections) — on `origin/step/DJy1ViGr-select-web-hosting` until task 1 merges it in
Ledger: `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime

## Summary

Three worker tasks and two gates that are already on the card.

- `deploy/deploy.py` keeps its command line and becomes a `gh-pages` publisher: it builds the publish tree from `is_deploy_path()` with git plumbing (no checkout, no temp copy of 35 MB), diffs it blob-by-blob against `origin/gh-pages`, fetches the live site over HTTPS and compares, prints the same four headings, and with `--upload` pushes one commit to `gh-pages`. No credential: the repo's own push access is the deploy credential.
- `deploy/verify.sh` is §11 as a script, with `--resolve` for the pre-DNS run.
- Footer links go `https://`; README, env example and tests follow; the ledger marks the FTP lines superseded.
- John's two gates (repo public + Pages source + custom domain + TTL 300; then merge, cutover, verify) get a runbook in the closing hand-off, distilled from §5.2, §7.2–7.3, §11 and §12.

## Starting point, and the first thing task 1 does

This worktree's branch was cut from `main` at `9524fad`, which is **four commits behind `origin/main`** (`deploy/backup.py` and two ledger lines) and does not have the select-web-hosting step at all. The migration plan, the comparison and the 2026-10-14/15 ledger lines live only on `origin/step/DJy1ViGr-select-web-hosting` (`0bcbe5f`), which already contains `origin/main`.

Task 1 therefore starts with:

```sh
git merge --no-edit origin/step/DJy1ViGr-select-web-hosting
```

A commit on a step branch is normal. It brings in `select-web-hosting/`, `deploy/backup.py` and the ledger lines this step must edit, and it means whichever of the two steps John merges to `main` first, the other lands cleanly (the commits are shared). This is not the step's own merge — that stays `/steprunner-merge` from the clone.

## Decision: build `gh-pages` with git plumbing; the commit log is the audit record

**Decision.** The publish tree is assembled in a temporary git index, written as a tree object, committed on top of `origin/gh-pages` and pushed — never checked out, never copied to a temp directory, never touching the user's index or working tree. The change oracle is the git blob id (`git hash-object`) compared with `git ls-tree -r origin/gh-pages`. The server manifest is retired; each `gh-pages` commit carries the audit fields as trailers, and `git log origin/gh-pages` is the history.

**Why.**
1. The blob id is exactly what git will compare on push, so the dry run's New/Changed/Unchanged is the push's truth, not an approximation of it (§4.6's "diff it against the tip of `gh-pages`").
2. Plumbing needs no second worktree and no `git checkout`, so it works from any worktree on Bishop and never risks switching the branch under a running worker.
3. A JSON manifest on the host existed because FTP had no checksum and no history. Git has both. Keeping the manifest would be a second, weaker copy of the branch.
4. `.nojekyll` and `CNAME` are written on every publish (§7.4), so a push can never drop the custom domain.

**Alternatives not taken.** A `git worktree add` of `gh-pages` into a temp dir plus `rsync` and `git add -A` works too, but adds and removes worktree entries in the shared repo on every deploy. Publishing from `main` with a `/docs` folder or a Jekyll `exclude:` list was ruled out by the ledger line (publish from a branch built by `is_deploy_path()`, never from the root of `main`).

The closing task writes this into the ledger under "Repo and runtime"; this task's sentinel carries it as a `decisions` entry, so the closing task checks for an existing line first.

## `deploy/deploy.py`

### Command line — unchanged (§4.1)

```
deploy/deploy.py                 # dry run: fetch gh-pages, build, compare, check live, print the plan
deploy/deploy.py --upload        # perform the plan: commit the publish tree to gh-pages and push
--force        publish even if nothing differs (new commit, same tree → Pages rebuilds); report lists every file as changed
--delete       also drop gh-pages files that are not in the deploy set (otherwise left alone, as today)
--allow-dirty  permit --upload with uncommitted deploy-set files
--env PATH     settings file (now optional, holds nothing secret)
--verbose      log every git command run and every URL fetched
```

Exit codes unchanged: 0 success (including a dry run); 1 transport failure (`git fetch`/`ls-remote`/`push` failing, non-fast-forward push); 2 usage (bad env file, dirty tree, no site files, remote URL not GitHub). The live HTTPS check **never** changes the exit code — see below.

### Settings (replaces credentials)

`resolve_settings()` keeps its precedence (process environment, then the env file, then defaults) and loses the password and `op` branches entirely. Keys:

| Key | Default | Meaning |
|---|---|---|
| `F3L_PAGES_REMOTE` | `origin` | git remote that hosts the site |
| `F3L_PAGES_BRANCH` | `gh-pages` | publish branch |
| `F3L_SITE_DOMAIN` | `www.f3lcontestseries.org` | contents of the `CNAME` file |
| `F3L_SITE_URL` | `https://www.f3lcontestseries.org` | base URL for the live check |

`F3L_DEPLOY_ENV`, `--env` and the default path `~/.config/f3l-series-website/deploy.env` keep working; the default file is optional. `parse_env_file()`, `load_env_file()` (with its permissions warning) and `Settings` stay. `op_read()`, `PASSWORD_KEY`, `OP_REF_KEY` and the `F3L_FTP_*` keys go. The stale `deploy.env` on Bishop (holding the FTP password) is simply ignored — its keys are unknown — and the README tells John he may delete it.

### What survives, what goes (§4.2)

Keep: `is_deploy_path()`, `collect_deploy_set()` (now records git blob id and size instead of sha256), `DEPLOY_*`, `Plan`, `compute_plan()` (re-typed, see below), `print_plan()`, `format_size()`, `upload_order()` (kept only to order the report), `git_state()`, `parse_porcelain_z()`, `parse_env_file()`, `load_env_file()`, `resolve_settings()`, `Settings`, `build_parser()`, `main()`, `UsageError`, the exit codes.

Delete: `FtpRemote`, `Remote`, `UPLOAD_SUFFIX`, `MANIFEST_*`, `build_manifest()`, `parent_dirs()`, `execute_plan()`, `is_managed_remote_path()`, `sha256_file()`, `FTP_TIMEOUT`, the `ftplib` import and the `all_errors` handler.

### Dry run, in order

1. Settings; `collect_deploy_set(root)`; `git_state(root)`; the dirty guard (only for `--upload`).
2. **Remote tip.** `git ls-remote --heads <remote> <branch>`. Non-zero exit → `exit 1` ("cannot reach origin"). Empty output → no publish branch yet: tip is `None`, remote tree is empty, print `No gh-pages branch on origin yet: every file counts as new.` Otherwise `git fetch <remote> <branch>` and read `FETCH_HEAD`.
3. **Remote tree.** `git ls-tree -r -l <tip>` → `{path: (blob, size)}`. The "Last deploy:" line comes from the tip commit's trailers (`git log -1 --format=%B`).
4. **Local blobs.** One call: `git hash-object --stdin-paths` (with `-w` only under `--upload`) fed the deploy-set paths → blob ids in order.
5. **Plan.** `compute_plan(local, remote, force)` is pure: path in local but not remote → New; blob differs (or `--force`) → Changed; same blob → Unchanged; path in remote but not local, and not one of the managed extras (`.nojekyll`, `CNAME`) → Remote-only. Size drift no longer exists as a case: a blob id is content.
6. **Live check** (§4.6's "what is live is measured, not assumed"). For every deploy-set path, `GET <F3L_SITE_URL>/<quoted path>` with `urllib`, a 20 s timeout and User-Agent `f3l-deploy/2`; compare the body's blob id with the local blob id. Print one `Live:` block: `matches gh-pages` / `N files differ from the local tree (listed)` / `not checked: <reason>` (TLS error, HTTP error, timeout). It is informational only: before cutover the name still points at iPage, whose certificate fails verification and which answers 465 to unknown agents (R11), and right after a push Pages takes up to a minute to build. ~35 MB per run is accepted for a one-code-path, honest measure. Each fetch is logged under `--verbose`.
7. `print_plan()` as today, then `exit 0` unless `--upload`.

### `--upload`

8. If nothing is New/Changed, nothing is Remote-only-with-`--delete`, and not `--force`: print `Nothing to do.` and `exit 0`.
9. Build the tree in a temporary index (`GIT_INDEX_FILE` pointing at a temp file):
   - `git read-tree <tip>` (or `--empty` on the first publish) so remote-only files are kept unless `--delete`;
   - `git update-index --index-info` fed `100644 blob <id>\t<path>` for every deploy-set file, plus `.nojekyll` (empty blob) and `CNAME` (`<F3L_SITE_DOMAIN>\n`), both written with `git hash-object -w --stdin`;
   - with `--delete`: `git update-index --force-remove` for each Remote-only path;
   - `git write-tree`.
10. `git commit-tree <tree> [-p <tip>] -m <message>`; the message is
    ```
    Publish <short source commit> from <branch name>

    Source-Commit: <full sha or unknown>
    Source-Dirty: true|false|unknown
    Deployed-By: jam@bishop
    Deployed-At: 2026-10-16T18:04:11Z
    Files: 31 (35,018,920 bytes)
    ```
11. `git push <remote> <commit>:refs/heads/<branch>`. A rejected push (someone else published in between) is `exit 1` with "fetch and re-run"; nothing on the branch changed.
12. Print the commit id, the branch, `https://github.com/<owner>/<repo>/deployments` (owner/repo parsed from the remote URL, ssh or https form) and `Re-run the dry run in a minute to confirm the live site matches.`

Deploy-set files whose blob already exists in the object store are not re-hashed by git; `-w` on the 35 MB set takes well under a second. Objects written by a failed run are unreferenced loose objects and `git gc` removes them.

### Report

Same headings and totals as today. "Remote:" becomes `Remote: origin/gh-pages @ <short tip>` (or `absent`), and "Last deploy:" reads the trailers. `Totals:` adds the live-check result on its own line. The `Live:` block lists at most the differing paths.

## `deploy/verify.sh`

§11 made runnable, so both gates are a command rather than a transcription:

```sh
deploy/verify.sh                                 # against https://www.f3lcontestseries.org
deploy/verify.sh --resolve 185.199.108.153       # pre-DNS: same URLs, Pages' address, real SNI and Host
deploy/verify.sh --base https://example.test     # another base (e.g. a fork's github.io URL)
```

POSIX sh + curl + openssl + dig, no other dependency. One line per check, `ok`/`FAIL`, non-zero exit if any FAIL. Checks, numbered as in §11: 1 the eight pages are 200; 2 `styles.css`, `assets/wagon.jpg`, `assets/PhxPilots.JPG` are 200 with sensible content types; 3 the bulletin `.doc` is 200, `application/msword`, 56,320 bytes; 4 a missing path is 404; 5 `assets/` is not a 200 listing; 6 the apex 301s to `https://www.…/` (public run only); 7 `http://` redirects to `https://` (public run only); 8 the certificate's SAN holds both names and the issuer is not RapidSSL (public run only; pre-DNS the check runs against the resolved address and reports the SAN for the eye); 9 MX and TXT for `f3lcontestseries.org` printed for a before/after diff; 10 a blank User-Agent and a custom one both get 200; 11 `results.html` sends no CSP or X-Frame-Options that would block the F3XVault iframes; 12 `Index.html` is 404; 13 the publish tree has no `decisions/`, `deploy/`, `README.txt` or step folder reachable (four probes, all 404 — added, not in §11). `robots.txt` (§11 item 13) is reported, not judged: 404 is correct on Pages.

The eye checks in §11 (browser, Word opening the `.doc`, the iframes rendering) stay in the hand-off as a list.

## Tests — `deploy/tests/test_deploy.py`

No network, and no fake FTP: the publish backend is git, so the tests use git. A `TempRemote` fixture makes a bare repository in a temp dir; a `TempSite` fixture makes a small site checkout (the `make_site()` tree) with that bare repo as `origin`. The CLI tests then run `deploy.main()` end to end: first dry run says no `gh-pages` yet and everything is New; `--upload` creates the branch with 31→6 files plus `.nojekyll` and `CNAME` and the right trailers; second run has nothing to do; one edit publishes one file; `--force` pushes a new commit with an identical tree; `--delete` removes a remote-only file only when asked; a dirty tree refuses `--upload`; unknown git state refuses; a non-fast-forward push exits 1 and leaves the branch alone; the remote-only extras are never reported. The live check is injected (`fetch=` callable on `main()`), tested for matches / differs / not-checked, and verified never to alter the exit code. Pure-function tests cover `compute_plan()` on blob maps, `parse_ls_tree()`, `parse_trailers()`, `publish_message()`, `github_repo_from_url()` for ssh and https remotes, and the existing deploy-set, env-file and porcelain tests, which keep their meaning. Target: ~45 tests, same runner (`python3 -m unittest discover -s deploy/tests`).

## Documentation

- `deploy/README.md` — rewritten around Pages: preview (unchanged), settings file (optional, no secret), the dry run and what each heading means now, the live check, `--upload` and what it pushes, `deploy/verify.sh`, "what is live" (`git log -3 origin/gh-pages` and the Deployments page), the custom-domain and DNS records as they must stay (four A records, `www` CNAME, custom domain = www, Enforce HTTPS on), the safety list (upload opt-in, dirty guard, `.nojekyll`/`CNAME` always written, never publishes from `main`), tests, and a Pages acceptance checklist replacing the FTP one. The SSH port-forward section stays.
- `deploy/deploy.env.example` — the four new keys, all commented out, and a note that the file is optional.
- `README.txt` — the "Preview and Deploy" paragraph says GitHub Pages instead of "the live site over FTP".
- `.gitignore` — unchanged (`deploy/deploy.env` stays ignored).

## Site-file cleanups (§10)

- The footer `<a href="http://www.f3lcontestseries.org">` on all eight pages → `https://www.f3lcontestseries.org`. One `sed` across the eight files; nothing else in the line changes.
- `http://www.soarabq.org/` on `index.html` and `schedule.html` stays. Measured 2026-10-15: `https://www.soarabq.org/` presents a certificate for another name (curl error 60) while `http://` answers 200.
- `deploy/backup.py` stays (out of scope until §13.1's final backup).

## Ledger (closing task)

Under § Repo and runtime, working on the file as merged from the hosting branch:

- The 2026-09-13 "VS Code upload-on-save FTP sync is to be replaced by a scripted build + deploy …" line and the 2026-09-13 "site deploy runs from Bishop … deploy.py … credentials in the environment …" line: prefix **superseded 2026-10-15** and point at the 2026-10-15 Pages line; the "from Bishop or John's Mac, by hand or by a worker, no Action" part is restated in the new line.
- The 2026-09-15 "FTP password lives in the 1Password item …" line: **superseded 2026-10-15** — no credential is needed to deploy; the env file is optional and holds no secret.
- The 2026-09-13 `smartftp.json` line and the 2026-09-15 history-rewrite line stay as they are (history, still true).
- New lines: the deploy-design decision above (skip if the runner already harvested it from this task's sentinel), and `op` 2.40.0 is installed on Bishop (plan §3 found the 2026-09-15 line wrong on that point).

## Pages setup and cutover — John's two gates (§5.2, §7.2–7.3, §11, §12)

Item 2 on the card (after the worker's first `gh-pages` push, which task 3 does):

1. Make the repo public. UI: Settings → General → Danger Zone → Change visibility. Or: `gh repo edit jmcneil86043/f3l-series-website --visibility public --accept-visibility-change-consequences`. This publishes `decisions/` and the step folders as repository content (accepted, ledger 2026-10-15).
2. Settings → Pages → Build and deployment: Source "Deploy from a branch", branch `gh-pages`, folder `/ (root)`. Or: `gh api -X POST repos/jmcneil86043/f3l-series-website/pages -f 'source[branch]=gh-pages' -f 'source[path]=/'`.
3. Custom domain: `www.f3lcontestseries.org` (the www name, not the apex — that is what gives the apex→www 301, C1). Or: `gh api -X PUT repos/jmcneil86043/f3l-series-website/pages -f cname=www.f3lcontestseries.org`. GitHub will show a DNS warning until cutover; that is expected. Do **not** tick Enforce HTTPS yet.
4. Pre-DNS gate (§7.2 step 5): `deploy/verify.sh --resolve 185.199.108.153` passes checks 1–5, 10–13 (the apex, http→https and certificate checks are public-run only). If Pages has not finished its first build, wait a minute and re-run.
5. Google Cloud DNS, zone `f3lcontestseries.org`: lower the TTL to **300** on exactly two records — the apex `A 65.254.248.183` and `www CNAME f3lcontestseries.org.` (both 14400 today). Touch no MX, no TXT, no NS. Write the current values down (they are in §12.1 too). This is T−48 h.
6. Confirm the zone has no other A/AAAA/CNAME for either name (C5 — stray records block certificate issuance).

Item 3 on the card, at least 48 hours later:

7. `dig +noall +answer @8.8.8.8 www.f3lcontestseries.org` shows TTL ≤ 300. If not, wait.
8. Merge this step's branch into `main` and push (`/steprunner-merge` on Bishop). Then, from the clone, `deploy/deploy.py` dry run must say 0 new / 0 changed — the merge does not change the site, and if it did, `--upload` first.
9. T−0, in Cloud DNS: `www.f3lcontestseries.org` CNAME → `jmcneil86043.github.io.` (TTL 300). Verify with dig and `deploy/verify.sh` (public, checks 1–5, 10–13). Then the apex: replace `A 65.254.248.183` with the four A records `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (TTL 300). www before apex (§5.3 rule 3).
10. Settings → Pages: wait for "certificate … issued" (minutes to an hour, C5), then tick **Enforce HTTPS**. Or poll `gh api repos/jmcneil86043/f3l-series-website/pages --jq .https_certificate.state` until `approved`, then `gh api -X PUT repos/jmcneil86043/f3l-series-website/pages -F https_enforced=true`.
11. `deploy/verify.sh` with no flags — every check, including the apex 301, http→https and the certificate. The eye checks: eight pages in a browser, the bulletin downloads and opens in Word, both F3XVault iframes on Results render. MX/TXT output unchanged from step 9's before-run.
12. T+48 h: raise the two changed records to **3600** (D6). Done; the old host is still serving its copy and is not touched.

**Rollback** at any point after step 9: put the two records back — apex `A 65.254.248.183`, `www CNAME f3lcontestseries.org.` — and clear the custom domain in Settings → Pages. Five minutes at TTL 300 (§12.2). Nothing on the old host was changed, so nothing is restored.

## Files

| Path | Status | Purpose |
|---|---|---|
| `deploy/deploy.py` | rewrite | gh-pages publisher: plumbing build, blob diff, live check, push; same CLI |
| `deploy/tests/test_deploy.py` | rewrite | tests against a temp bare repo and a temp site; injected live fetch |
| `deploy/verify.sh` | new | §11 checks with `--resolve` |
| `deploy/README.md` | rewrite | Pages workflow, settings, DNS as it must stay, acceptance checklist |
| `deploy/deploy.env.example` | rewrite | four optional keys |
| `README.txt` | edit | one line |
| `index.html` … `host.html` (8 pages) | edit | footer `https://` |
| `decisions/F3L-Series-Web-Site-decisions.md` | edit | superseded marks, two new lines |
| `migrate-…/step-outputs/*-output-notes.md`, `*-handoff.md` | new | per task |
| `gh-pages` branch on origin | new | the published tree; never merged, never checked out |

## Implementation tasks

1. **Merge the hosting branch in; rewrite `deploy/deploy.py` and its tests.** `git merge --no-edit origin/step/DJy1ViGr-select-web-hosting` first. Then the script per the sections above (remove FTP, add `fetch_remote_tree()`, `local_blobs()`, `compute_plan()` on blob maps, `check_live()`, `build_publish_tree()`, `publish()`, `publish_message()`/`parse_trailers()`, `github_repo_from_url()`, settings keys) and the test file (temp bare repo + temp site fixtures, CLI flow, pure functions, injected live check). Run the suite; run the real dry run from this worktree (expect: no gh-pages yet, 31 new, live not checked or 465). Commit. Size: 2 files (~450 + ~450 lines), ~30 min — the big one; it is one file set and must not be split.
2. **`deploy/verify.sh`, footer links, docs.** The verify script; the eight-page `sed`; `deploy/README.md`, `deploy/deploy.env.example`, `README.txt`. Run `deploy/verify.sh --base http://www.f3lcontestseries.org` against the old host to prove the script itself works (checks 6–8 will FAIL there; that is the point of the old host). Commit. Size: 12 files, ~20 min.
3. **Closing.** Run the tests; `deploy/deploy.py` dry run then `--upload` from the committed branch (first publish: creates `gh-pages`; expect 31 files + `.nojekyll` + `CNAME`); `git ls-tree -r origin/gh-pages` shows exactly those 33 paths and none of `decisions/`, `deploy/`, `README.txt`, step folders; second dry run says nothing to do. Ledger edits per § Ledger. Output notes with the dry-run and ls-tree evidence, and the hand-off for the two gates carrying the runbook above verbatim with the §12 restore values. Commit. Size: 3 files + ledger, ~15 min.

Checklist names as they should appear on the step card, after this task's item and before the card's existing items 2 and 3:

1. `[needs-you] Review the design and plan`
2. `Merge origin/step/DJy1ViGr-select-web-hosting into this branch, then rewrite deploy/deploy.py as the gh-pages publisher (same CLI and flags; git-plumbing build of the publish tree; dry run against origin/gh-pages and the live site) and rewrite deploy/tests/test_deploy.py against a temp bare repo`
3. `Add deploy/verify.sh (migration plan §11 with --resolve), switch the eight footer self-links to https://, rewrite deploy/README.md and deploy/deploy.env.example for Pages, update the README.txt line`
4. `Closing: run the tests, do the first deploy/deploy.py --upload to create gh-pages and check its tree, mark the 2026-09-13/15 FTP ledger lines superseded and add the deploy-design and op lines, write the output notes and the cutover hand-off for the two gates, commit`
5. `[needs-you] Try the new functions yourself`

The card's existing items ("[needs-you] Make the repo public …" and "[needs-you] Merge the branch …") follow item 5 and are the cutover; the task 3 hand-off is written for them.

## Open decisions

- **Merging a sibling step branch into this one** (task 1's first command) is my call, not the ledger's. It is the only way this branch can carry the plan and the ledger lines it must edit; the alternative — edit a ledger copy that lacks the 2026-10-15 lines and let John resolve the conflict at merge — is worse. If John would rather merge the hosting step to `main` first and rebase this branch, say so at review and task 1 does `git merge origin/main` instead.
- **Live check cost.** Fetching the full 35 MB on every dry run is deliberate (one code path, honest measure). If that is too slow on Bishop's link, the cheaper variant is a `HEAD` per asset comparing `Content-Length` and a `GET` only for the text files; same report, ten more lines.
- **`--force` meaning.** "New commit, same tree, Pages rebuilds" is the useful reading now that nothing is re-sent. If the reviewer would rather `--force` stay cosmetic (list all as changed, publish only if anything differs), it is one condition.
- **"Try the new functions yourself" sits before the Pages gate**, so at that point the dry run and `--upload` work but the site is not yet served; the task 3 hand-off says what to try then and what waits for the gates. The runner inserts the items after this task's own; if they land out of order, read the names above as the intended order.
