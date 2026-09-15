# Output notes — Design the approach and write the implementation plan

Task: https://trello.com/c/6PnyeVnB   Step: https://trello.com/c/DMARfx61   Date: 2026-09-13

## What was produced
- Spec: `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-spec.md` — no material open questions, so the design went ahead.
- Design: `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md` — stdlib Python `deploy/deploy.py` (dry-run default, server-side manifest for change detection, atomic uploads), `deploy/preview.sh`, credentials from env / `~/.config/f3l-series-website/deploy.env` / `op read`. Decision: deploy runs from Bishop by hand or by a step worker; no GitHub Action.
- Risks: `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-risks.md`.
- Two implementation tasks plus the review and try items, requested via the sentinel's `checklist_items_to_add`.

## Facts established while orienting
- Site links are all relative; serving the checkout root is a valid preview.
- `ftp.mcneilco.com` is a FatCow ProFTPD: FEAT lists MLSD, MLST, SIZE, MDTM, MFMT, UTF8; `AUTH TLS` → 504, so plain FTP only.
- `smartftp.json` is not on this machine (John's original folder is not here); host/user/path taken from the card.
- No `op` CLI on this machine; Bishop status unknown. The design does not require it (env file is the primary path).

## Not done / for the reviewer
- The runner inserts the new checklist items after this task's item, so the existing credentials `[needs-you]` item lands after "Try the new functions yourself". See design § Open decisions.
