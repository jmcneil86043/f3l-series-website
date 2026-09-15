# Output notes — Add deploy/preview.sh, deploy.env.example, deploy/README.md, .gitignore and ledger entry; run tests and commit

Task: https://trello.com/c/LLTDPUqU   Step: https://trello.com/c/DMARfx61   Date: 2026-09-13
Design implemented: `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md` (implementation task 2, the closing task)

## What was produced
- `deploy/preview.sh`: runs `python3 -m http.server --bind 127.0.0.1` on the checkout. The port defaults to 8080 or comes from the first argument. It prints the URL.
- `deploy/deploy.env.example`: the three non-secret keys with their defaults, a blank `F3L_FTP_PASSWORD=`, and a commented `F3L_FTP_PASSWORD_OP_REF=` for 1Password. The file says where the real copy goes (`~/.config/f3l-series-website/deploy.env`, mode 600).
- `deploy/README.md` covers:
  - preview, and reviewing from the Mac through an SSH port-forward
  - first-time setup on the deploying machine (password or 1Password reference) and the order settings are resolved in
  - dry run and `--upload`, the other flags and exit codes
  - what gets published, and how the manifest decides what changed
  - safety properties and the tests
  - a 7-point acceptance checklist for the first live run (for the "Try the new functions yourself" item)
- `.gitignore`: adds `deploy/deploy.env`, and `__pycache__/` (running the tests creates it under `deploy/`).
- `README.txt`: the old "Testing Locally" and "When Uploading to AWS S3 or Apache" sections are replaced with a short pointer to `deploy/README.md`.
- Ledger: nothing added. `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime already has the "deploy runs from Bishop, no GitHub Action" line (harvested by the runner in ab2e39d). The earlier line ("…runnable on Bishop or as a GitHub Action") is narrowed by it, not reversed, so it is not marked superseded.

## Verified
- `python3 -m unittest discover -s deploy/tests`: 48 tests, OK.
- `deploy/preview.sh 18089`: all 7 pages, `styles.css`, all 21 `assets/` images referenced by the pages, and the bulletin `.doc` download returned HTTP 200.
- With an empty environment and no env file, `deploy/deploy.py` exits 2 with a one-line message naming the password variable and the env file path. It doesn't prompt and doesn't connect. It does the same with a copy of the example file (blank password).
- The example file parses with the script's own parser, including the 1Password reference that contains spaces.
- `git check-ignore deploy/deploy.env` matches, and `smartftp.json` is still ignored.

## Not done
- No live FTP run. There are no credentials on this machine yet; the next item, `[needs-you] Put the FTP credentials…`, covers that. The live run is steps 3–7 of the acceptance checklist in `deploy/README.md`.
