# Request — Write deploy/deploy.py and its unit tests

Task: https://trello.com/c/F6QxhKE1 (id 6aa7243ec72e899b1236f77d)
Step: https://trello.com/c/DMARfx61 — Step 0: Design and implement an FTP deployment system with local preview
Received: 2026-09-13

## Ask, as received

[RC Sailplanes & Helis] Write deploy/deploy.py and its unit tests (deploy set, manifest plan, FTP upload, credentials, dry-run CLI)

Implementation task 1 of `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md`:
deploy-set collection, hashing, manifest model, pure plan function, `Remote` interface with `FtpRemote`
and `FakeRemote`, credential resolution (env → env file → `op read`), CLI with dry-run default, plain
report output; tests in `deploy/tests/test_deploy.py`, no network.

Out of this task's scope (next checklist item): `deploy/preview.sh`, `deploy/deploy.env.example`,
`deploy/README.md`, `.gitignore`, `README.txt`, ledger entry.
