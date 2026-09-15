# Risks — Step 0: Design and implement an FTP deployment system with local preview

Step: https://trello.com/c/DMARfx61   Written: 2026-09-13 by task 6aa71e6ebea377855670e678
Design: `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md`

## What breaks while this change is in flight
(none)

## What could go wrong with this change
- **Wrong remote dir publishes into the wrong place on the hosting account** · likelihood low · impact high · noticed by: the first dry run lists every file as new and no remote-only files where some are expected; `--verbose` shows the CWD · mitigation/rollback: the script refuses to create the remote dir, so a typo fails instead of publishing; check `F3L_FTP_REMOTE_DIR` against `smartftp.json` before the first `--upload`.
- **`--delete` removes server content the repo never had** · likelihood low · impact high · noticed by: the dry run's remote-only list · mitigation/rollback: off by default; run a dry run first and read that list; restore from John's local folder or the host's backup if it happens.
- **Half-finished deploy leaves the live site mixed between two versions** · likelihood low · impact medium · noticed by: the script exits 1 mid-run; the old manifest is still on the server · mitigation/rollback: per-file rename makes each page atomic; re-run `--upload` and the remaining files go out; `--force` rebuilds everything from the checkout.
- **Manifest drifts from reality because someone edits files on the server directly (VS Code sync still enabled on John's Mac)** · likelihood medium · impact low · noticed by: a size mismatch shows as "changed" in the dry run; a same-size edit is silently overwritten by the next deploy · mitigation/rollback: disable upload-on-save once the script is in use; `--force` when in doubt.
- **Password leaks into a worktree or the repo** · likelihood low · impact high · noticed by: `git status` shows `deploy/deploy.env`; `git log -p` grep · mitigation/rollback: default env file lives under `~/.config`, `deploy/deploy.env` is gitignored, the script never prints the password; if committed, rotate the FTP password on the host.
- **Deploying an unreviewed or uncommitted tree** · likelihood medium · impact medium · noticed by: the manifest's `git_dirty` / `git_commit` fields on the server · mitigation/rollback: dirty guard refuses `--upload` without `--allow-dirty`; redeploy from the intended commit.
- **`op read` hangs or prompts in a non-interactive worker session** · likelihood medium · impact low · noticed by: the deploy stalls with no output · mitigation/rollback: prefer the env file on Bishop; the 1Password path is for interactive use; the script runs `op` with a timeout and exits 2 on failure.
