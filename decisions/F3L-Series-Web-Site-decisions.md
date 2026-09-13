# Decisions — F3L Series Web Site

Scope: the F3L Contest Series website (RC Sailplanes & Helis board, list "F3L Series Web Site").
One line per settled decision: date · decision · why · link to the full reasoning.
Index, not a store — the reasoning lives in the linked note, never here.
Never delete: mark reversals **superseded** and point forward. Read this file before proposing anything.

## Repo and runtime

- **2026-09-13 · The site's git repo is `~/Projects/TPG/F3L Series/WebSite/F3l_series` (John's existing folder), symlinked into the workspace as `projects/f3l-series-website`, and pushed to the private GitHub repo `jmcneil86043/f3l-series-website`.** Why: John keeps his folder layout; StepRunner needs a `projects/<name>` for `[project:f3l-series-website]` and a GitHub ssh URL for a member machine to clone. The sibling `Media/` folder (photo zips, Word drafts) is deliberately outside the repo.
- **2026-09-13 · Every step on this list runs on Bishop (`[account:john-bishop]`); the RC Sailplanes & Helis board is registered to the box so the box dispatches them over SQS.** Why: this project is the practicality test for running StepRunner work on Bishop before the StepRunner repos themselves move there. John reviews worktrees remotely (VS Code over SSH first; sync-to-laptop if that fails).
- **2026-09-13 · `smartftp.json` (the VS Code FTP-sync config, which holds the FTP password) is gitignored and untracked; deploy credentials never live in the repo.** Why: the repo is on GitHub; credentials belong in the environment / 1Password of the machine that deploys.
- **2026-09-13 · The VS Code upload-on-save FTP sync is to be replaced by a scripted build + deploy with a local preview (Step 0), runnable on Bishop or as a GitHub Action.** Why: a worker on Bishop cannot use the VS Code extension, and a deploy needs a dry run, a preview, and a reproducible path from a worktree.
- **2026-09-13 · The site deploy runs from Bishop (or John's Mac) as deploy/deploy.py invoked by hand or by a step worker, with credentials in the environment or ~/.config/f3l-series-website/deploy.env; no GitHub Action is wired.** Why: The review already happens in a worktree on Bishop, the host only speaks plain FTP so a cloud runner adds exposure for no gain, and an explicit command keeps a human go and an audit trail; an Action can reuse the same script later. → `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md`

## Content
