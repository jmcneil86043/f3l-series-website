# Output notes — Write deploy/deploy.py and its unit tests

Task: https://trello.com/c/F6QxhKE1   Step: https://trello.com/c/DMARfx61   Date: 2026-09-13
Design implemented: `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md` (implementation task 1)

## What was produced
- `deploy/deploy.py`: Python 3.9+, standard library only. Contains the deploy-set collection (top-level `*.html`, `styles.css`, `assets/**`, no dotfiles), sha256 hashing, and a pure `compute_plan`. Also the `Remote` interface with `FtpRemote` (passive FTP, walks the tree with MLSD, uploads to `<name>.uploading` and renames it over the target, creates `assets/` subdirs, refuses a missing remote dir), the manifest (`.f3l-deploy-manifest.json`, written last), credentials (environment, then the env file, then `op read`, then non-secret defaults), the dirty-tree guard, and the CLI with dry run as the default.
- `deploy/tests/test_deploy.py`: 48 `unittest` tests, no network. They cover:
  - the deploy set and what it excludes
  - every row of the design's plan table
  - upload order
  - env-file parsing, credential order, the 1Password ref, the permissions warning
  - git porcelain parsing, plus a real temp git repo for the dirty check
  - end-to-end `main()` against a `FakeRemote`: dry run sends nothing, first upload, second run has nothing to do, a one-page edit sends one file, `--force`, `--delete`, a failed upload leaves the old manifest (exit 1), the dirty refusal (exit 2), a missing password (exit 2)
  - `FtpRemote`'s own FTP commands against an in-memory `FakeFtp`

  Run: `python3 -m unittest discover -s deploy/tests` → 48 OK in 0.15 s. I also changed the key rules on purpose (size drift, manifest write, rename, the dirty guard, dry run, deploy-set filter) and the tests failed each time.
- Real checkout: the deploy set is 30 files, 33.4 MB, matching the design.

## Choices made within the design (for the reviewer)
- **Remote dotfiles** (`.htaccess`, `.ftpquota`, …) are never reported as remote-only and never deleted, even with `--delete`. They are server config, and local dotfiles are never deployed.
- **`--force`** re-sends every file. Files missing from the manifest or server still show as "new", not "changed".
- **Dirty-tree refusal** exits 2 (fixed by committing or a flag), like other usage errors. If git can't report the tree's state (not a checkout, no git), `--upload` is also refused unless `--allow-dirty` is given, and the manifest then records `git_dirty: true`.
- **Nothing to do**: if an upload run finds nothing new, changed or to delete, it does not rewrite the manifest. The manifest keeps recording the last deploy that actually sent something.
- **FTP errors** (login refused, transfer aborted, timeout) exit 1 and say the manifest was not updated. Credentials are resolved before any connection, so a missing password exits 2 without touching the network.
- **Upload order**: assets first, then `styles.css`, then pages. A page never goes live before the images it references.
- **Rename fallback**: if the server refuses to rename over an existing file, the script deletes the target and renames again. ProFTPD normally allows the overwrite, so this is a fallback only.
- **`--verbose`** uses ftplib's debug log, which masks the `PASS` command.

## Not done
- No live FTP run: there are no credentials on this machine yet (that is the later `[needs-you]` credentials item). The live smoke test belongs to the "Try the new functions yourself" item.
- Left for the next checklist item: `deploy/preview.sh`, `deploy/deploy.env.example`, `deploy/README.md`, `.gitignore`, `README.txt`, and the ledger entry. The ledger already has the "Bishop, no Action" line under "Repo and runtime", so the closing task should not add it again.
