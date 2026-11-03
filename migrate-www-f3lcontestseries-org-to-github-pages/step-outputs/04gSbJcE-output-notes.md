# Output notes — task 04gSbJcE (rewrite deploy.py + tests for GitHub Pages)

**Task:** Merge the hosting step's branch, then rewrite `deploy/deploy.py` as the
gh-pages publisher (same CLI and flags; git-plumbing build of the publish tree;
dry run against `origin/gh-pages` and the live site) and rewrite
`deploy/tests/test_deploy.py` against a temp bare repo.

**Status:** done — committed as `a0710a4` on this step branch (merge commit
`b11b2ed` immediately before it). Not pushed, not merged — those belong to the
later `[needs-you]` gate.

## The merge was `git merge origin/main`, not the named branch

`origin/step/DJy1ViGr-select-web-hosting` no longer exists: that step was
already merged to `main` (merge commit `cc51e26`, "Merge step DJy1ViGr
(step/DJy1ViGr-select-web-hosting)") and its remote branch was auto-deleted,
per the workspace's landed-branch rule. This is exactly the fallback the
design anticipated ("task 1 does `git merge origin/main` instead"). The merge
had one conflict, in `decisions/F3L-Series-Web-Site-decisions.md` (both sides
added lines at the same spot); resolved by keeping all lines in chronological
order, including this step's 2026-10-15 deploy-design line.

## What the new deploy.py does (per `ffsosn1p-design.md`)

- **Change oracle:** git blob ids. Local deploy set is hashed with one
  `git hash-object --stdin-paths` call; the remote side is
  `git ls-tree -r -l` of the gh-pages tip. No server manifest, no credential
  beyond the repo's own push access.
- **Publish:** a temporary `GIT_INDEX_FILE` starts from `read-tree <tip>` (or
  `--empty`), gets `update-index --index-info` for the deploy set plus
  `.nojekyll` and `CNAME` (written on every push, so a push can never drop the
  custom domain), optional `--force-remove` of remote-only files under
  `--delete`, then `write-tree` → `commit-tree` → `push <remote> <sha>:refs/heads/gh-pages`.
  Never checks anything out, never touches the user's index or worktree.
- **Commit message trailers** (the audit record): `Source-Commit`,
  `Source-Dirty`, `Deployed-By`, `Deployed-At` (UTC, `%Y-%m-%dT%H:%M:%SZ`),
  `Files: N (bytes)`. The next run prints `Last deploy: …` parsed from the
  tip's trailers.
- **CLI/flags unchanged:** dry run is the default; `--upload`, `--force`,
  `--delete`, `--allow-dirty`, `--env PATH`, `--verbose`. Exit codes 0/1/2 as
  before: 1 now covers git fetch/ls-remote/push failures and non-fast-forward
  pushes (the error adds "someone else published in between; fetch and re-run");
  2 covers bad env file, dirty tree, no site files, missing remote, and a
  remote URL that isn't a GitHub URL (checked via the *stored* remote URL —
  `git config remote.<n>.url` — because `git remote get-url` applies
  `insteadOf` rewrites, which would break both the check and this test suite's
  fixture trick).
- **Settings:** `F3L_PAGES_REMOTE` (default `origin`), `F3L_PAGES_BRANCH`
  (default `gh-pages`), `F3L_SITE_DOMAIN` (default
  `www.f3lcontestseries.org`, the CNAME content), `F3L_SITE_URL` (default
  `https://www.f3lcontestseries.org`). Precedence: process env → env file →
  default. `F3L_DEPLOY_ENV` and `--env` still work; the default file
  `~/.config/f3l-series-website/deploy.env` is optional and holds nothing
  secret. The old `F3L_FTP_*` keys, `FtpRemote`, the manifest and the
  `op_read` password helper are gone.
- **Live check:** GETs each deploy-set path (20 s timeout, UA `f3l-deploy/2`)
  and compares the body's computed blob id to the local blob id. Reports
  `Live: matches origin/gh-pages`, `Live: N files differ…`, or
  `Live: not checked: <reason>`. Informational only — it never changes the
  exit code and never blocks a push.

## Test suite (50 tests, all passing, ~4 s)

`python3 -m unittest discover -s deploy/tests` from the repo root:

```
Ran 50 tests in 4.510s
OK
```

No network and no real remote. The fixture builds a temp **bare** repo as the
stand-in for GitHub and a temp site checkout whose `origin` is the GitHub-form
URL `git@github.com:jmcneil86043/f3l-series-website.git` with a per-repo
`url.<bare-path>.insteadOf` rewrite, so all of ls-remote/fetch/push go to the
local bare repo while the stored URL still satisfies the GitHub check. The
live check is injected (`fetch=`) and defaults to a fetch that refuses to
connect. Coverage:

- **CLI end-to-end** (first dry run: 6 new, `No gh-pages branch…`; first
  `--upload`: branch created with 8 entries = 6 files + `.nojekyll` + `CNAME`,
  correct CNAME body, empty `.nojekyll`, full trailer block; second run:
  `Nothing to do.`; one edit: one Changed; `--force`: new commit, identical
  tree; stray remote-only file: listed, kept without `--delete`, dropped with
  it; dirty tree refuses (exit 2 naming the file), `--allow-dirty` publishes
  with `Source-Dirty: true`; unknown git state refuses; unreachable remote:
  exit 1 `cannot reach origin`; failing live fetch never changes the exit
  code; `F3L_PAGES_REMOTE` reaches a second remote, via env and via `--env`).
- **Pure functions:** `compute_plan` (new/changed/unchanged/force/
  remote-only-excludes-extras/upload order), `parse_ls_tree`,
  `parse_trailers`, `publish_message` (exact format),
  `github_repo_from_url`, `blob_id` (cross-checked against real
  `git hash-object`), `format_size`, env-file parsing/precedence/permissions,
  `parse_porcelain_z`, `check_live` (match/differs/not-checked/never-raises/
  URL quoting).
- **Direct plumbing:** `build_publish_tree` (first publish; keeps remote-only
  unless `delete`), and `publish()` against a stale tip → `GitError` with the
  non-fast-forward note, branch tip unchanged.
- **`git_state`** against a real temp checkout: dirty tracking counts only
  deploy-set paths (incl. untracked and rename sources), not-a-checkout →
  all-None.

## Real dry run from this worktree (evidence)

```
$ python3 deploy/deploy.py        # exit 0
DRY RUN (nothing will be sent; pass --upload to publish)
Local:  /Users/jam/steprunner/worktrees/f3l-series-website/aet0F8Yq @ b11b2ed24d0eb0e869d5ca98e2db20096678492f
Remote: origin/gh-pages @ absent
No gh-pages branch on origin yet: every file counts as new.
New (31, would be uploaded): … (8 pages, styles.css, assets/ incl. highstart/)
Totals: 31 new, 0 changed, 0 unchanged, 0 remote-only; 33.4 MB to send
Live: not checked: cannot connect ([SSL: CERTIFICATE_VERIFY_FAILED]
  certificate verify failed: Hostname mismatch, certificate is not valid
  for 'www.f3lcontestseries.org'. (_ssl.c:1147))
```

Matches the design's expectation: no gh-pages yet, **31 new** (35,018,920
bytes), live not checked because the old iPage certificate still fails
verification for this hostname — it will report properly once the domain
points at Pages. (The dry run's `git ls-remote` reached GitHub fine, so push
access is in order.)

## For the following tasks

- The **first `--upload`** will create `gh-pages` as a root commit (no parent)
  and push 31 files + 2 extras; it also triggers the first Pages build.
  Afterward, re-running the dry run is the cutover check (the live check will
  then compare against the real site and should say `matches origin/gh-pages`
  within a minute or two of the build).
- `deploy/verify.sh` (the next item) can reuse the same settings resolution
  and the `--verbose` git-command log; `deploy/README.md` and
  `deploy/deploy.env.example` still describe the FTP world and belong to the
  following rewrite task.
- One behavior to know: a remote that exists but can't be *reached* (network
  down) is exit 1; a remote whose stored URL isn't a GitHub URL is exit 2 —
  the script will only ever publish to GitHub.
