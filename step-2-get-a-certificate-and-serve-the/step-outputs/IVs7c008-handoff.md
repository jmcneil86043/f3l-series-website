# Hand-off: Review the design and plan for Step 2 (HTTPS)

## Goal
Serve www.f3lcontestseries.org over HTTPS with a certificate the host issues and renews, redirect plain HTTP and the bare domain to `https://www.f3lcontestseries.org/…`, and switch the site's own links to https://. The redirect is a tracked `.htaccess` published by the Step 0 deploy.

## Current status
Spec, design and risks are written and committed on the step branch. No site or tooling file has been changed. The step is waiting on this review.

## What happened
- Probed the host from this machine: FTP banner says FatCow; site and FTP hosts are both in Newfold's `65.254.248.0/24`; port 443 on the site's IP already serves the site's pages but presents a `*.bizland.com` wildcard certificate, which is Newfold's shared SSL front end. That means the certificate is a control-panel action, not something installed by hand. `.htaccess` is honoured (Apache returns 403 on it). Details in the design § Facts.
- Audited the site: the only self-reference is the footer link on all eight pages; no canonical/og:url tags; nothing loads over http://, so no mixed content once HTTPS is on.
- Found that `deploy/deploy.py` excludes every dotfile, so publishing `.htaccess` needs a small, tested tooling change (root `.htaccess` only, uploaded last in a run).
- Wrote the spec (no material open questions), the design (route A: free panel certificate; route B1: buy the host's certificate; redirect rules; tooling change; a closing task that refuses to publish until the certificate is verified live), the risks doc, and this hand-off.
- Placed the implementation items on the step checklist, in order, after my own item. The pre-existing `[needs-you] Confirm the hosting provider…` item could not be moved and sits last.

## Files & paths
- Spec: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-spec.md`
- Design: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-design.md`
- Risks: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-risks.md`
- Request as received: `step-2-get-a-certificate-and-serve-the/step-outputs/IVs7c008-request.md`
- Output notes: `step-2-get-a-certificate-and-serve-the/step-outputs/IVs7c008-output-notes.md`
- Files the plan will touch: new `.htaccess`; the footer of `index.html`, `schedule.html`, `results.html`, `postal.html`, `about.html`, `howto.html`, `host.html`, `highstart.html`; `README.txt`; `deploy/deploy.py`, `deploy/tests/test_deploy.py`, `deploy/README.md`; `decisions/F3L-Series-Web-Site-decisions.md`.

## Pending checklist items
1. `[needs-you] Review the design and plan` (this gate)
2. `Teach deploy/deploy.py to publish a root .htaccess (deploy set, uploaded last, tests, deploy/README.md)`
3. `Add .htaccess with the HTTPS and www redirect, switch the footer self-link on all 8 pages to https://, add the README.txt line; dry run and commit, no upload`
4. `[needs-you] Enable the certificate for f3lcontestseries.org in the hosting control panel (design § Certificate, route A else B1) and confirm https://www.f3lcontestseries.org/ loads with no warning`
5. `Closing: confirm the certificate is live, run tests and dry run, publish with deploy.py --upload, verify the redirects and every page over HTTPS, ledger lines, notes, commit`
6. `[needs-you] Merge the branch into main (task-dispatcher merge-step RbsRQzYp), then try the new functions yourself`
7. `Confirm the hosting provider and control-panel access for www.f3lcontestseries.org and note which certificate options it offers [needs-you]` (pre-existing; its substance is covered by items 1 and 4)

## Open decisions
From the spec's open questions: (none).

From the design's `## Open decisions`:
- **Checklist order.** The pre-existing `[needs-you] Confirm the hosting provider…` item lands after the merge/try item because existing items are never reordered. The certificate gate (item 4) is where that confirmation is actually used. Either tick the old item when you do item 4, or move it yourself.
- **Who runs `--upload`.** The closing worker publishes, because it verifies the certificate and the redirects in the same run. Say if you would rather run `deploy/deploy.py --upload` yourself in the try item.
- **Bare domain → www (rule 1).** Included so there is one canonical HTTPS address. Strike it if you want `https://f3lcontestseries.org/` to serve directly.
- **Panel "Force HTTPS" toggle.** If the panel offers one, the design leaves it off and uses the repo's `.htaccess`. Say if you prefer the toggle; then no `.htaccess` ships and task 2 is unnecessary.
- **Canonical tags and HSTS.** Neither is added. Say if you want `<link rel="canonical">` per page or a short-max-age HSTS header.

Risks in brief (full list in the risks doc): the redirect must never go live before the certificate (tasks 2–3 never upload; the closing task checks `curl https://…` without `-k` first); a redirect loop behind the proxy is guarded by requiring both `HTTPS` and `X-Forwarded-Proto` to say "not TLS", and is checked with curl straight after upload; rollback for any redirect problem is comment-out, commit, `--upload`; renewal must be confirmed automatic at the certificate gate, else the ledger carries a due date.

## The ask
Review the design and plan. Approve as is, or answer the open decisions above. While you are in the hosting panel, note whether it offers a free certificate for `f3lcontestseries.org` (route A) or only paid ones (route B1); that answer is used at item 4.

## How to respond
Add your feedback as a comment on the task card for this gate, then clear its label. Clearing the label is what moves the step; reopening this session does nothing. If everything is fine, a comment saying "approved" is enough.
