# Request — Design the approach and write the implementation plan

Task: https://trello.com/c/6PnyeVnB (id 6aa71e6ebea377855670e678)
Step: https://trello.com/c/DMARfx61 — Step 0: Design and implement an FTP deployment system with local preview
Received: 2026-09-13

## Ask, as received

Design and implement, for the static F3L Contest Series site (seven HTML pages, styles.css, assets/, no build step):

1. a local preview so a reviewer can look at a worktree's version of the site before it goes live;
2. a deploy script that publishes the site over FTP, with a dry-run mode that lists what would change and only uploads what differs;
3. a decision, recorded in `decisions/F3L-Series-Web-Site-decisions.md`, on whether the deploy runs from Bishop (script invoked by a step worker or by hand) or as a GitHub Action, plus the corresponding wiring.

Constraints given: credentials from environment variables or a 1Password item on the deploying machine, never from the repo; `smartftp.json` stays gitignored and is only a local reference for host, user and remote path; shell or Python, no framework; simple and auditable.

This task's own scope: write the spec, design and implementation plan; derive the implementation tasks for the step checklist. The next checklist item (`[needs-you]` credentials placement) is the user's.
