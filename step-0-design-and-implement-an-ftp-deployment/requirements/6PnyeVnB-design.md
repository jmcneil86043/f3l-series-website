# Design — Step 0: Design and implement an FTP deployment system with local preview

Step: https://trello.com/c/DMARfx61   Written: 2026-09-13 by task 6aa71e6ebea377855670e678
Spec: `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-spec.md`
Ledger: `decisions/F3L-Series-Web-Site-decisions.md`

## Summary

Two small stdlib-only tools in a new `deploy/` folder at the repo root, plus one gitignored env file outside the repo on the deploying machine:

- `deploy/preview.sh` — serves the checkout on localhost with Python's built-in HTTP server.
- `deploy/deploy.py` — computes the deploy set, compares it against a manifest the script itself keeps on the server, prints a plan, and (only with `--upload`) uploads the differing files atomically over FTP and rewrites the manifest.

The deploy runs from Bishop (or John's Mac), invoked by hand or by a step worker. No GitHub Action is wired. Reasoning in § Decision.

## Decision: deploy from Bishop, not a GitHub Action

**Decision.** The publish is a script run on the machine that holds the credentials (Bishop, or John's Mac), invoked explicitly by a person or a step worker. No GitHub Action is added now.

**Why.**
1. The preview and the review already happen in a worktree on Bishop; deploying from the same place means what was reviewed is what ships, before or after merge, with no second pipeline to reason about.
2. The host only speaks plain FTP (probed: `AUTH TLS` → 504). Sending that password from a GitHub-hosted runner adds a third party and a public-cloud source IP for no gain; from Bishop it is the same exposure the VS Code sync has today.
3. A deploy-on-push Action removes the human "go" and turns every merge into a publish; the card asks for a dry run and an auditable path, which fits a deliberate command better.
4. The script is the same either way. If an Action is ever wanted, it is a ten-line workflow that sets four secrets and runs `deploy.py --upload`. Nothing here forecloses it.

**Wiring for the chosen side.** Credentials come from the process environment or from `~/.config/f3l-series-website/deploy.env` (mode 600, outside every worktree so all worktrees share it), with an optional 1Password reference resolved by `op read`. Details in § Credentials.

The closing task writes this into the ledger under "Repo and runtime"; the sentinel for this task also carries it as a `decisions` entry, so the closing task must check the ledger for an existing line before adding one.

## Deploy set

Explicit include list, in one place near the top of `deploy.py`:

- every `*.html` at the repo root;
- `styles.css`;
- everything under `assets/`, recursively.

Excluded by construction: anything else at the root (`README.txt`, `decisions/`, `deploy/`, `requirements/`, `step-outputs/`, `.claude/`, `.git`, `smartftp.json`), and any file or directory whose name starts with `.` (`.DS_Store`). Remote paths mirror local paths relative to the repo root, under the remote dir. The repo root is found from the script's own location (`deploy/..`), so it works from any worktree without arguments.

Current size: 7 pages, 1 stylesheet, 22 asset files, about 33 MB.

## Change detection: a manifest on the server

Git checkouts and worktrees give files fresh mtimes, so mtime comparison is useless here, and FTP has no checksum command. The script therefore keeps its own manifest on the server:

`<remote dir>/.f3l-deploy-manifest.json`
```json
{
  "version": 1,
  "deployed_at": "2026-09-13T21:04:11Z",
  "git_commit": "bf397e7…",
  "git_dirty": false,
  "deployed_by": "jam@bishop",
  "files": { "index.html": {"sha256": "…", "size": 5991}, "assets/wagon.jpg": {"sha256": "…", "size": 6873237} }
}
```

Plan computation, given local files (path → sha256, size), the remote manifest (or none) and a remote listing (path → size from MLSD, recursive walk of the remote dir):

| Case | Classification |
|---|---|
| No manifest on server | every file is **new** (first run uploads everything and creates the manifest) |
| Local path absent from manifest, or absent from listing | **new** |
| Manifest hash differs from local hash | **changed** |
| Hash equal but listed remote size differs from manifest size | **changed** (someone edited the server behind the manifest) |
| Hash and size equal | **unchanged** |
| Listed remote path not in local deploy set (manifest itself excluded) | **remote-only** (reported; deleted only with `--delete`) |
| `--force` | every file is **changed** |

The manifest is also the audit trail: which commit, when, by whom, and whether the tree was dirty. It is a public file on the web root; it contains only paths, hashes and a commit id, nothing sensitive.

## Upload behaviour

- Passive mode; timeouts on connect and transfer; one connection for the whole run.
- Each file is uploaded to `<name>.uploading` in its directory, then renamed over the target (RNFR/RNTO), so a half-transferred page never serves.
- Remote subdirectories under `assets/` are created as needed. The remote dir itself must already exist; the script refuses to create it (guards against a mistyped remote path publishing into the wrong place).
- The manifest is written last, only after every upload succeeded. A failed run therefore leaves the old manifest, and the next run re-sends whatever was in flight.
- `--delete` removes remote-only files (never directories, never the manifest) after the uploads. Off by default.
- Dirty-tree guard: if `git status --porcelain` shows changes to any deploy-set file, the script refuses `--upload` unless `--allow-dirty`. Dry-run is always allowed. The manifest records `git_dirty`.
- Output is a plain per-file report grouped by classification, then totals, then (upload only) the per-file transfer log and the manifest's commit id. Exit code 0 on success and on a clean dry-run; 1 on any failure; 2 on usage or missing credentials.

## Command-line interface

```
deploy/deploy.py                 # dry run (the default): plan only, nothing sent
deploy/deploy.py --upload        # perform the plan
deploy/deploy.py --upload --force        # re-send everything, rebuild manifest
deploy/deploy.py --upload --delete       # also remove remote-only files
deploy/deploy.py --upload --allow-dirty  # permit uncommitted deploy-set changes
deploy/deploy.py --env PATH      # env file other than the default
deploy/deploy.py --verbose       # FTP command log (password never echoed)
```

Dry run as the default is deliberate: a worker that forgets a flag inspects rather than publishes.

## Credentials

Resolution order for each of the four settings, first hit wins:

1. process environment: `F3L_FTP_HOST`, `F3L_FTP_USER`, `F3L_FTP_PASSWORD`, `F3L_FTP_REMOTE_DIR`;
2. the env file (`--env PATH`, else `$F3L_DEPLOY_ENV`, else `~/.config/f3l-series-website/deploy.env`), a `KEY=value` file parsed by the script (not sourced, so no shell surprises); the script warns if the file is group- or world-readable;
3. for the password only: if `F3L_FTP_PASSWORD_OP_REF` is set (e.g. `op://Private/F3L FTP/password`), run `op read <ref>` and use its output. This is the 1Password path; it needs the `op` CLI signed in on that machine.

Defaults if nothing sets them: host `ftp.mcneilco.com`, user `jmcneil`, remote dir `/f3l_series` (the values in the card, none of them secret). The password has no default; missing password → exit 2 with a one-line message naming the env var and the env file path. The password is never printed, never written to disk by the script, and never passed on a command line.

A tracked `deploy/deploy.env.example` shows the four keys with the password blank and a comment pointing at the 1Password alternative. `.gitignore` gains `deploy/deploy.env` so a copy dropped in the worktree by habit cannot be committed either.

## Preview

`deploy/preview.sh [port]` runs:

```
python3 -m http.server --bind 127.0.0.1 --directory "<repo root>" "${1:-8080}"
```

and prints the URL. It serves the whole checkout (the non-site files are harmless on localhost). All site links are relative (verified: no absolute `href`/`src` in any page), so the pages, images and the `.doc` download work as served. Remote review from John's Mac is an SSH port-forward, documented in `deploy/README.md`:

```
ssh -L 8080:127.0.0.1:8080 bishop   # then open http://localhost:8080/
```

No preview build is produced: with no build step, the checkout is the build.

## Files

| Path | Status | Purpose |
|---|---|---|
| `deploy/deploy.py` | new | plan + FTP upload + manifest + credentials; Python 3.9+, stdlib only (`ftplib`, `hashlib`, `json`, `argparse`, `subprocess`) |
| `deploy/tests/test_deploy.py` | new | `unittest` tests for the plan logic against an in-memory fake remote and a temp tree |
| `deploy/preview.sh` | new | local server wrapper |
| `deploy/deploy.env.example` | new | documented key names, password blank |
| `deploy/README.md` | new | preview, dry-run, deploy, first-time setup on Bishop, remote review over SSH |
| `.gitignore` | edit | add `deploy/deploy.env` |
| `README.txt` | edit | replace the "Testing Locally" and "When Uploading" sections with a pointer to `deploy/README.md` |
| `decisions/F3L-Series-Web-Site-decisions.md` | edit | the Bishop-not-Action entry |

`deploy.py` is structured so the FTP session sits behind a tiny `Remote` interface (`read_manifest`, `listing`, `upload`, `write_manifest`, `delete`, `mkdir`) with a `FakeRemote` in the tests; the plan function is pure (inputs: local map, manifest, listing, flags → lists). That is what makes the logic testable without an FTP server on the box.

## Testing

- Unit (`python3 -m unittest discover -s deploy/tests`): deploy-set collection from a temp tree (dotfiles and non-site files excluded); plan cases in the table above; `--force`; manifest absent; remote-only detection with the manifest excluded; env-file parsing and resolution order (password from env beats file; missing password exits 2); dirty-tree guard.
- Live smoke, only once credentials exist (checklist item 4): `deploy.py` dry run shows every file as new (no manifest yet); `--upload` sends everything and writes the manifest; a second dry run reports nothing to do; the live site renders. Recorded in `deploy/README.md` as the acceptance checklist, and performed in the final `[needs-you]` item.

## Implementation tasks

1. **Write `deploy/deploy.py` and its unit tests** — deploy-set collection, hashing, manifest model, pure plan function, `Remote` interface with `FtpRemote` (passive, MLSD walk, atomic upload via rename, manifest read/write, delete) and `FakeRemote`, credential resolution (env → env file → `op read`), CLI with dry-run default and the flags above, plain report output. Tests in `deploy/tests/test_deploy.py` cover the plan table, credential order, dirty guard and deploy-set exclusion; no network. Size: 2 files, ~350 lines, ~25 min.
2. **Add preview, env example, docs, ledger entry, and commit** — `deploy/preview.sh`, `deploy/deploy.env.example`, `deploy/README.md` (setup on Bishop including the 1Password option, preview, dry run, deploy, SSH port-forward, acceptance checklist), `.gitignore` line, `README.txt` pointer, the ledger line under "Repo and runtime" (skip if the runner already added it from this task's sentinel), run the unit tests, commit. Size: 6 files, ~15 min.

Checklist names as they should appear on the step card, after this task's item:
1. `[needs-you] Review the design and plan`
2. `Write deploy/deploy.py and its unit tests (deploy set, manifest plan, FTP upload, credentials, dry-run CLI)`
3. `Add deploy/preview.sh, deploy.env.example, deploy/README.md, .gitignore and ledger entry; run tests and commit`
4. `[needs-you] Put the FTP credentials where the deploy will read them …` (the pre-existing item, moved here)
5. `[needs-you] Try the new functions yourself`

The credentials item comes before the try item because the live smoke in `deploy/README.md` needs the env file in place.

## Open decisions

- **Plain FTP.** The host refuses TLS, so the password crosses the network in clear on every deploy, exactly as the VS Code sync does today. If the FatCow account offers SFTP, switching is a later step (the `Remote` interface is the seam); not pursued here.
- **Remote-only files.** Anything in `/f3l_series` that the repo does not contain is reported and left alone. If the first dry run shows leftovers John wants gone, `--delete` on that one deploy is the tool; the default stays report-only.
