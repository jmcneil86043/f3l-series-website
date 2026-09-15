# Spec — Step 0: Design and implement an FTP deployment system with local preview

Step: https://trello.com/c/DMARfx61   Written: 2026-09-13 by task 6aa71e6ebea377855670e678
Derived from: the step card description (snapshot in `step-outputs/6PnyeVnB-request.md`); `decisions/F3L-Series-Web-Site-decisions.md` (all four "Repo and runtime" entries); the repo as checked out at bf397e7 (no project plan doc exists yet).

## What this step delivers
After this step, anyone with the FTP password on the deploying machine can look at a worktree's copy of the F3L Contest Series site in a browser before it goes live, see exactly which files a publish would add or change without touching the server, and then publish only those files to www.f3lcontestseries.org with one command. The choice of where the publish runs from is written down in the decisions ledger, and the credentials live outside the repo.

## In scope
- A local preview of the site from any checkout or worktree.
- A deploy over FTP to the existing host, with a dry-run that reports what would change and an upload that sends only what differs, leaving an audit trail of what was published and from which commit.
- The Bishop-vs-GitHub-Action decision, recorded in the ledger, with the wiring for the chosen side (where the script reads credentials on the deploying machine).
- Documentation short enough that a step worker or John can run preview, dry-run and deploy cold.

## Out of scope
- Any change to the site's content, layout or file structure.
- A build step, templating, minification or image optimisation (the site has none and needs none).
- Retiring or deleting files already on the server that the repo does not know about (reported, not removed, unless explicitly asked per deploy).
- Placing the credentials themselves (the `[needs-you]` item that follows this task).
- Moving the host, changing protocol (e.g. to SFTP) or any hosting-account change.

## Success criteria
- From a worktree on Bishop or John's Mac, one command serves the site locally and the pages, images and the bulletin download all work in a browser.
- With no credentials configured, the dry-run still fails clearly and never prompts for or prints a password.
- With credentials configured, a dry-run against the live server lists added/changed/unchanged/remote-only files and uploads nothing (server unchanged afterwards).
- A real deploy after a one-page edit uploads that page only, the live site shows the edit, and a second deploy immediately afterwards reports nothing to do.
- Nothing credential-like appears in `git log -p`, and `smartftp.json` stays untracked.
- The ledger has a dated entry saying where the deploy runs from and why.

## Constraints from the ledger
- "`smartftp.json` (the VS Code FTP-sync config, which holds the FTP password) is gitignored and untracked; deploy credentials never live in the repo." — `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime, 2026-09-13.
- "The VS Code upload-on-save FTP sync is to be replaced by a scripted build + deploy with a local preview (Step 0), runnable on Bishop or as a GitHub Action." — same section, 2026-09-13.
- "Every step on this list runs on Bishop (`[account:john-bishop]`) … John reviews worktrees remotely (VS Code over SSH first; sync-to-laptop if that fails)." — same section, 2026-09-13.

## Assumptions
- Host `ftp.mcneilco.com`, user `jmcneil`, remote path `/f3l_series` (from the card description; `smartftp.json` is not present on this machine). Not material: all three are configuration the script reads at run time, so a wrong value is a one-line fix.
- The server only offers plain FTP (probed 2026-09-13: FEAT lists MLSD/SIZE/MDTM/MFMT, `AUTH TLS` returns 504). Not material: this is what the current VS Code sync already uses; TLS would be a flag, not a redesign.
- The deploy set is exactly the top-level `*.html`, `styles.css` and `assets/` (no dotfiles, no `.DS_Store`); everything else in the repo stays local. Not material: the list is one place in the script and the reviewer can adjust it.
- Whether the deploy runs from Bishop or a GitHub Action is for this design to decide, since the card asks for the decision as a deliverable and the following checklist item says "per the design". Not material as an open question: the design decides and the review item is where it gets challenged.
- Files on the server that the repo does not contain are left alone by default. Not material: a flag covers the other behaviour.

## Open questions (what)
(none)
