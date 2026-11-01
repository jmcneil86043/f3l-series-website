# Output notes — task TrT2UGML (Closing: tests, first publish, ledger, notes)

**Task:** Run the tests, do the first `deploy/deploy.py --upload` to create `gh-pages` and
check its tree, mark the 2026-09-13/15 FTP ledger lines superseded and add the
deploy-design and `op` lines, write the output notes and the cutover hand-off for the two
gates, commit.

**Status:** done — committed on this step branch. The `gh-pages` branch now exists on
origin (first publish, commit `32859f04`); the step branch itself is not pushed past
`8edead5` and not merged — those belong to the later `[needs-you]` gates.

## What was done

- **Tests:** full suite green (below).
- **First publish:** `deploy/deploy.py --upload` from the committed branch (`8edead5`)
  created `gh-pages` on origin as commit `32859f04` — 31 deploy-set files + `.nojekyll`
  (empty) + `CNAME` (`www.f3lcontestseries.org`). Pushed; the repo is still private and
  nothing is served until John sets the Pages source.
- **Tree check:** `git ls-tree -r origin/gh-pages` is exactly those 33 paths; none of
  `decisions/`, `deploy/`, `README.txt` or any step folder is in the tree.
- **Second dry run:** `0 new, 0 changed, 31 unchanged, 0 remote-only`; the `Last deploy:`
  line reads the tip commit's trailers.
- **Ledger** (`decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime):
  - the 2026-09-13 "VS Code upload-on-save FTP sync …" line — prefixed **superseded
    2026-10-15**, points at the 2026-10-15 Pages line;
  - the 2026-09-13 "site deploy runs from Bishop … credentials … no GitHub Action" line —
    prefixed **superseded 2026-10-15**; the "from Bishop or John's Mac, by hand or by a
    worker, no Action" part is restated as still holding, only the credentials clause is
    gone;
  - the 2026-09-15 "FTP password lives in the 1Password item …" line — prefixed
    **superseded 2026-10-15** (no deploy credential anymore; env file optional, no
    secret), and flags its "op not installed" clause as wrong;
  - new line: **`op` (1Password CLI) 2.40.0 is installed on Bishop** (measured 2026-10-15,
    per `select-web-hosting/migration-plan.md` §3, which found the 2026-09-15 line wrong
    on that point).
  - The deploy-design line (git-plumbing build, trailers as the audit trail) was already
    harvested by the runner from the design task's sentinel — it is the 2026-10-15 line
    "deploy.py publishes the site by building the gh-pages tree with git plumbing …", so
    it was **not** duplicated. The 2026-09-13 `smartftp.json` line and the 2026-09-15
    history-rewrite line are untouched, as the design's Ledger section requires.

## Evidence

**Test suite:**

```
$ python3 -m unittest discover -s deploy/tests
Ran 50 tests in 4.497s
OK
```

**First dry run** (before the publish):

```
DRY RUN (nothing will be sent; pass --upload to publish)
Local:  /Users/jam/steprunner/worktrees/f3l-series-website/aet0F8Yq @ 8edead5d11823d7f41558f3fab3ae8797892f8d5
Remote: origin/gh-pages @ absent
No gh-pages branch on origin yet: every file counts as new.
New (31, would be uploaded): … (31 files, 33.4 MB)
Totals: 31 new, 0 changed, 0 unchanged, 0 remote-only; 33.4 MB to send
Live: not checked: cannot connect ([SSL: CERTIFICATE_VERIFY_FAILED] … not valid for 'www.f3lcontestseries.org' …)
```

**`--upload`:** committed `32859f04c03850cad4dd15b1d04b3c61d3b662b5 (first publish)`,
pushed `origin/gh-pages`. Commit message:

```
Publish 8edead5 from step/aet0F8Yq-migrate-www-f3lcontestseries-org-to-github-pages

Source-Commit: 8edead5d11823d7f41558f3fab3ae8797892f8d5
Source-Dirty: false
Deployed-By: jam@beastboy
Deployed-At: 2026-11-01T13:12:54Z
Files: 31 (35,018,928 bytes)
```

**Tree check:**

```
$ git ls-tree -r --name-only origin/gh-pages | wc -l
33
$ git ls-tree -r --name-only origin/gh-pages | grep -E '^(decisions/|deploy/|README\.txt|select-web-hosting/|migrate-|step-0)'
(nothing)
$ git show origin/gh-pages:CNAME
www.f3lcontestseries.org
$ git cat-file -s origin/gh-pages:.nojekyll
0
```

**Second dry run** (after the publish):

```
Remote: origin/gh-pages @ 32859f0
Last deploy: 2026-11-01T13:12:54Z of 8edead5 by jam@beastboy
Unchanged (31, skipped): …
Totals: 0 new, 0 changed, 31 unchanged, 0 remote-only; 0 B to send
Live: not checked: cannot connect ([SSL: CERTIFICATE_VERIFY_FAILED] …)
```

The `Live:` line is "not checked" (not a failure) exactly as designed: the name still
resolves to the old iPage host, whose certificate is for another name. It flips to a real
comparison after the DNS cutover.

**`--resolve` run immediately after the publish** (status snapshot, not yet the pre-DNS
gate proof — the repo's Pages source is not set until John's gate):

```
$ deploy/verify.sh --resolve 185.199.108.153     # exit 1
FAIL 1   pages not 200: … (all 8, 404 — Pages has no source configured yet)
FAIL 2   stylesheet/assets wrong: … (404)
FAIL 3   bulletin 404 …
ok   4   missing path is a 404
ok   5   assets/ has no directory listing (404)
skip 6   apex -> www 301  (pre-DNS)
skip 7   http -> https  (pre-DNS)
info 8   certificate presented at 185.199.108.153 (for the eye, not judged):
         subject=CN=*.github.io issuer=… Let's Encrypt …
info 9   mail records (diff before/after): MX 10 mxb.mailgun.org. 10 mxa.mailgun.org.
         | TXT "v=spf1 include:mailgun.org ~all"
FAIL 10  user agents: plain=404 custom=404
FAIL 11  content-security-policy: default-src 'none' … (the 404 page's CSP)
ok   12  Index.html is a 404 (case sensitivity intact)
ok   13  decisions/, deploy/, README.txt and a step folder are all 404
info     robots.txt 404
11 checks: 4 ok, 5 failed, 2 skipped
```

The 404s on 1/2/3/10 are the "no source configured" state, not a build failure — re-run
after the Pages source is set (gate step 4). The check-9 line above is the **pre-cutover
baseline** for the MX/TXT diff.

## For the two gates

The full runbook for both `[needs-you]` gates — with the §12 rollback values — is in
`migrate-www-f3lcontestseries-org-to-github-pages/step-outputs/TrT2UGML-handoff.md`.
Everything the worker side of this step owed is now on `origin/gh-pages` and in the
branch; what remains is John's: make the repo public, set the Pages source and custom
domain, drop the TTLs, merge and cutover, verify.
