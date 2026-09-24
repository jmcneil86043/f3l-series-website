# Spec — Step 2: Get a certificate and serve the site over HTTPS

Step: https://trello.com/c/RbsRQzYp   Written: 2026-09-24 by task 6ab523bfa0e4fe24df0a8d48
Derived from: the step card description (snapshot in `step-2-get-a-certificate-and-serve-the/step-outputs/IVs7c008-request.md`); `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime; `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md` (deploy set, dotfile rule, `--delete` rule, manifest); `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/xa6BE0FD-output-notes.md` (link audit, first live deploy); the live site and host as probed on 2026-09-24 (recorded in the design § Facts).

## What this step delivers
A visitor who types the site's address, or follows any old link to it, ends up on https://www.f3lcontestseries.org with the browser's padlock and no warning: plain-HTTP addresses and the bare domain forward there. The certificate is issued and renewed by the hosting provider without anyone having to remember a date. The site's own links point at the HTTPS address, and the redirect is a file in the repository, published by the Step 0 deploy like any other file.

## In scope
- Establishing what the hosting account behind ftp.mcneilco.com offers for certificates, and enabling one there (John, in the control panel).
- HTTP → HTTPS redirect, and bare domain → www, as a tracked `.htaccess` published by the deploy.
- The deploy-tooling change needed to publish that one dotfile, with tests.
- The site's self-links switched to https://; docs and ledger updated.
- Verifying the live result: certificate, redirects, every page over HTTPS.

## Out of scope
- Changing DNS, the registrar (Squarespace Domains, Google Cloud DNS name servers) or putting a CDN such as Cloudflare in front of the site.
- HSTS preload or a long HSTS max-age (see Assumptions).
- External links, e.g. `http://www.soarabq.org/` on the home and schedule pages: not the site's own.
- Securing the FTP transport; it stays plain FTP (Step 0 design § Open decisions).
- Any other content change.

## Success criteria
- `https://www.f3lcontestseries.org/` and every page load with a certificate the browser trusts, issued for the site's own name rather than the host's `*.bizland.com` wildcard.
- `http://www.f3lcontestseries.org/<page>`, `http://f3lcontestseries.org/<page>` and `https://f3lcontestseries.org/<page>` each answer with one permanent redirect to the same page on `https://www.f3lcontestseries.org/`, and the redirect never loops.
- No page pulls anything over http:// (no mixed-content warning).
- The footer link on every page reads `https://www.f3lcontestseries.org/`.
- The provider renews the certificate itself, and the ledger records where in the panel it lives and how renewal works.
- A deploy dry run after the publish reports nothing to send, and the server manifest records the step's final commit.

## Constraints from the ledger
- "The site deploy runs from Bishop (or John's Mac) as deploy/deploy.py invoked by hand or by a step worker, with credentials in the environment or ~/.config/f3l-series-website/deploy.env; no GitHub Action is wired." — `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime, 2026-09-15.
- "The VS Code upload-on-save FTP sync is to be replaced by a scripted build + deploy with a local preview (Step 0)…" — same section, 2026-09-13. The redirect file goes through that deploy, not through the panel's file manager.
- "`smartftp.json` … is gitignored and untracked; deploy credentials never live in the repo." — same section, 2026-09-13. Nothing from the hosting panel (passwords, private keys) enters the repo.

## Assumptions
- The provider is FatCow (a Newfold brand; help pages now redirect to Network Solutions). The FTP banner says `fatcow FTP Server Ready`, the site and FTP hosts share the 65.254.248.0/24 range, and port 443 already serves the site behind a `*.bizland.com` wildcard. John confirms at the pre-existing `[needs-you]` item; not material, it changes only which panel page he opens.
- Whether the panel's certificate is free (Let's Encrypt-style, auto-renewed, as FatCow's own docs say) or must be bought from the host is decided at the certificate gate; the design carries both routes. Not material to what is delivered: either way the host installs and renews it, and the site-side changes are identical.
- The canonical host is `www.f3lcontestseries.org` (what the pages, the card and the footer already use); the bare domain folds into it. Not material: one rewrite rule, struck at review if unwanted.
- No `<link rel="canonical">` tags exist and none are added; after the redirect, https-www is the only form the server serves. Not material: one line per page if wanted later.
- No HSTS header in this step. Not material: one header line, added later once HTTPS has run cleanly for a while.
- The publish (`deploy.py --upload`) is run by the closing worker after it has verified the certificate is live, not by John in the try item, because the redirect must never go live ahead of the certificate and the worker can check both in one run. Not material: John can say at review that he prefers to run the upload himself.
- The redirect lives in a tracked `.htaccess` rather than a panel "force HTTPS" toggle (if the panel has one). Not material to the outcome; the file is auditable and reproducible, the toggle is noted as an alternative.

## Open questions (what)
(none)
