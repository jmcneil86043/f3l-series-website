# Preview and deploy

Three tools for the F3L Contest Series site (www.f3lcontestseries.org). All work from any
checkout or worktree with no arguments. `deploy.py` needs Python 3.9+ and git; `verify.sh`
needs curl, openssl and dig; nothing else.

- `deploy/preview.sh`: serves this checkout on localhost so you can look at it before it goes live.
- `deploy/deploy.py`: publishes the site to GitHub Pages and sends only the files that changed.
  By default it does a **dry run**: it prints the plan and pushes nothing.
- `deploy/verify.sh`: runs the migration plan's §11 checks against the live site.

These replace the VS Code upload-on-save sync (`smartftp.json`) and the old FTP deploy. The
deploy runs from Bishop or John's Mac, started by hand or by a step worker. No GitHub Action
is involved; the reason is in `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime.

## Preview

```sh
deploy/preview.sh          # http://127.0.0.1:8080/
deploy/preview.sh 8081     # another port
```

The script serves the checkout as it is, uncommitted edits included. There is no build step,
and every link in the site is relative, so pages, images and the bulletin download all work.
Stop it with Ctrl-C.

**Reviewing a worktree on Bishop from your Mac.** Start the preview on Bishop inside the
worktree, then forward the port:

```sh
ssh -L 8080:127.0.0.1:8080 bishop     # leave this open
```

Then open http://localhost:8080/ on the Mac. The server only listens on 127.0.0.1, so the
tunnel is the only way in. (VS Code Remote-SSH forwards the port automatically when the
preview starts in its terminal.)

## Deploy

```sh
deploy/deploy.py                          # dry run: show the plan, push nothing
deploy/deploy.py --upload                 # publish the changed tree to gh-pages
```

A dry run fetches `origin/gh-pages` and prints every file under one of these headings:

- **New**: not on gh-pages yet
- **Changed**: its content differs from what was last deployed (git blob id, so byte-exact)
- **Unchanged**: skipped
- **Remote-only**: on gh-pages but not in the repo; left alone unless you pass `--delete`

Totals follow, then `Last deploy:` parsed from the gh-pages tip's commit trailers (which
source commit, who, when, dirty or clean, how many files). If nothing changed it just says
`Nothing to do.` Run the dry run, read it, then run the same command with `--upload`.

Other flags:

| Flag | Effect |
|---|---|
| `--force` | a new commit even when the tree is unchanged, so Pages rebuilds |
| `--delete` | also delete remote-only files |
| `--allow-dirty` | allow `--upload` when site files have uncommitted changes (recorded as `Source-Dirty: true`) |
| `--env PATH` | use this env file |
| `--verbose` | log the git commands |

Exit codes: 0 means success, including a dry run. 1 means a git failure: the remote can't be
reached, or the push was rejected as non-fast-forward — someone else published in between;
fetch and re-run. 2 means a usage problem: bad env file, uncommitted site files on
`--upload`, no site files, no remote, or a remote whose URL isn't a GitHub URL — the script
will only ever publish to GitHub.

### The live check

After the plan, the script GETs every deploy-set path on the live site and compares the body
to the local content (UA `f3l-deploy/2`, 20 s timeout). It reports
`Live: matches origin/gh-pages`, `Live: N files differ…`, or `Live: not checked: <reason>`.
Informational only: it never changes the exit code and never blocks a push. Before the DNS
cutover it says `not checked`, because the old host's certificate is not valid for this name;
a minute or two after a push it confirms the Pages build has landed.

### What gets published

- every `*.html` at the repo root
- `styles.css`
- everything under `assets/`

31 files. On every push the script also writes `.nojekyll` (empty) and `CNAME`
(`www.f3lcontestseries.org`), so a push can never drop the custom domain or the Jekyll
opt-out. Nothing whose name starts with `.` is published from the repo; everything else stays
local: `README.txt`, `deploy/`, `decisions/`, step folders. The list is `is_deploy_path()`
at the top of `deploy.py`.

### Settings (optional, no secret)

The repo's own push access is the deploy credential; there is no password. All four keys are
optional — the defaults are correct:

| Key | Default | Meaning |
|---|---|---|
| `F3L_PAGES_REMOTE` | `origin` | the remote to push `gh-pages` to |
| `F3L_PAGES_BRANCH` | `gh-pages` | the branch Pages serves from |
| `F3L_SITE_DOMAIN` | `www.f3lcontestseries.org` | the `CNAME` content |
| `F3L_SITE_URL` | `https://www.f3lcontestseries.org` | the base the live check GETs |

Precedence: process environment → env file → default. The env file is `--env PATH`, else
`$F3L_DEPLOY_ENV`, else `~/.config/f3l-series-website/deploy.env` — all optional, parsed as
`KEY=value`, never sourced by a shell. The old `deploy.env` on Bishop (with the FTP
password) is simply ignored — its `F3L_FTP_*` keys are unknown — and can be deleted any time.

### What is live

```sh
git fetch origin gh-pages && git log -3 origin/gh-pages
```

Each publish commit's trailers are the audit record (`Source-Commit`, `Source-Dirty`,
`Deployed-By`, `Deployed-At`, `Files: N (bytes)`). GitHub's build status for the branch is
on the repo's Deployments page:
https://github.com/jmcneil86043/f3l-series-website/deployments

### The Pages setup that must stay

- The repo is **public** (a GitHub Pages requirement).
- The Pages source is the **`gh-pages` branch, root** — never the root of `main`.
- Custom domain `www.f3lcontestseries.org`; Enforce HTTPS on, once the certificate is issued.
- DNS (Google Cloud DNS, unchanged except these): four A records at the apex —
  185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 — and `www` a CNAME to
  `jmcneil86043.github.io.`. TTL 3600, lowered to 300 for the cutover window.
- The MX and TXT (mailgun) records are never touched.

The cutover itself and the decommissioning of the old host are later cards
(`select-web-hosting/migration-plan.md` §5 and §13).

## Safety

- Publish is opt-in. A command without `--upload` never pushes.
- `--upload` refuses when site files have uncommitted changes, so what ships matches a commit.
- Each publish is one whole-tree commit on `gh-pages`; if the push is rejected, nothing has
  changed on the remote.
- `.nojekyll` and `CNAME` are rewritten on every push, so a push can never drop the custom
  domain or the Jekyll opt-out.
- The published tree is only ever built from the deploy set — never from the root of `main`.
- Nothing secret crosses the network: the credential is the repo's own push access.

## Verify

`deploy/verify.sh` runs the migration plan's §11 checks — one line per check,
`ok` / `FAIL` / `info` / `skip`; exit 0 if nothing failed, 1 if any check failed, 2 on bad
usage.

```sh
deploy/verify.sh                            # public run after the cutover: all 13 checks
deploy/verify.sh --resolve 185.199.108.153  # pre-DNS: the www name forced at a Pages address
deploy/verify.sh --base URL                 # another base: a fork's github.io URL, the old host
```

In the `--resolve` run the checks are aimed at the real SNI and Host, so routing is tested as
a browser would see it; checks 6-7 are skipped (the public names still point at the old
host) and 8 is reported for the eye, because the certificate is not issued until DNS points
at Pages. With `--base`, checks 6-8 are judged only when the base is the real name.

The by-eye checks (every page in a browser, the bulletin opening in Word, the F3XVault
iframes rendering) live in the migration plan's hand-off, not in the script.

## Safety copy of the old FTP account

`deploy/backup.py` mirrors the old FTP account into a local folder; it stays for the final
pre-decommissioning backup (migration plan §13.1). Note it is out of sync with the Pages
rewrite: it still expects the FTP settings and `FTP_TIMEOUT` that the rewrite removed, so it
needs updating before it can run. The old host is untouched until the decommissioning card,
which owns that fix.

## Tests

```sh
python3 -m unittest discover -s deploy/tests
```

The tests build a temp bare repository as the stand-in for GitHub and don't touch the
network.

## Acceptance checklist (first live run)

1. `deploy/preview.sh`, then open the site: every page loads, images show, and on "Host a
   Contest" the bulletin template downloads.
2. `deploy/deploy.py` (dry run) lists every file as new — `gh-pages` doesn't exist yet — and
   the live check says `not checked` (the old host's certificate is not valid for this name).
3. `deploy/deploy.py --upload` pushes. `git ls-tree -r origin/gh-pages --name-only` lists 33
   paths: the 31 site files, `.nojekyll`, `CNAME`. None of `decisions/`, `deploy/`,
   `README.txt` or a step folder.
4. `deploy/deploy.py` again: `Nothing to do.`
5. Edit one page, commit, and run `deploy/deploy.py --upload`. The dry run before and after
   shows exactly that one page changed and nothing else to send.
6. The publish commit's trailers (`Source-Commit`, `Deployed-By`, …) agree with
   `git log origin/gh-pages` and the repo's Deployments page.
