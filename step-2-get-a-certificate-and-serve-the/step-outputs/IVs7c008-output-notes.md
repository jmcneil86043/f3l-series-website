# Output notes — Design the approach and write the implementation plan

Task: https://trello.com/c/IVs7c008   Step: https://trello.com/c/RbsRQzYp   Date: 2026-09-24

## What was produced
- Spec: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-spec.md` — no material open questions, so the design went ahead.
- Design: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-design.md` — certificate enabled in the FatCow/Newfold panel (route A free, else B1 paid), tracked `.htaccess` with a loop-safe HTTP→HTTPS rule and a bare-domain→www rule, footer self-links to https://, `deploy.py` publishes the root `.htaccess` (uploaded last), closing task verifies the certificate before it publishes.
- Risks: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-risks.md`.
- Review hand-off: `step-2-get-a-certificate-and-serve-the/step-outputs/IVs7c008-handoff.md`.
- Request as received: `step-2-get-a-certificate-and-serve-the/step-outputs/IVs7c008-request.md`.
- Six checklist items placed on the step card after this task's item, in the order listed in the design § Implementation tasks.

## Facts established while orienting
- Host: FatCow (Newfold). `ftp.mcneilco.com` banner `220 fatcow FTP Server Ready`; site IP `65.254.248.183`, FTP IP `65.254.248.220`. Name servers Google Cloud DNS, registrar Squarespace Domains, domain expires 2028-07-02.
- Port 443 on the site's IP already serves the site's pages behind `CN=*.bizland.com` (DigiCert RapidSSL, valid 2026-08-12 → 2027-02-26): Newfold's shared SSL front end. The per-domain certificate is a panel action.
- `GET /.htaccess` → 403, so `.htaccess` is honoured. `/.well-known/acme-challenge/…` → plain 404, so an HTTP-01 challenge could be served over FTP if route B2 were ever needed.
- The front proxy adds `X-Request-ID` and a `request_id` cookie; hence the two-condition redirect rule (`HTTPS` and `X-Forwarded-Proto`).
- FatCow's docs: free SSL enabled per domain, covers subdomains, not combinable with a paid certificate on the same domain. FatCow help now redirects to `networksolutions.com/help`; the panel may carry either brand. Auto-renewal is to be confirmed at the certificate gate.
- Site: one self-reference per page (footer `http://www.f3lcontestseries.org`), no canonical tags, no `http://` in any `src`. One external `http://www.soarabq.org/` link left alone.
- `deploy.py` excludes all dotfiles from the deploy set and from `--delete`; the server manifest exists (2026-09-21, `jam@Mika`), so deploys are incremental now.

## Sources read
- `README.txt`, `.gitignore`, all eight `*.html` (grep for `http://`, `https://`, canonical, `og:url`, `<base>`), `styles.css` (grep only)
- `decisions/F3L-Series-Web-Site-decisions.md` (as supplied in the task context)
- `step-0-design-and-implement-an-ftp-deployment/requirements/6PnyeVnB-design.md`
- `step-0-design-and-implement-an-ftp-deployment/step-outputs/6PnyeVnB-output-notes.md`, `LLTDPUqU-output-notes.md`
- `step-1-schedule-updates-cvrc-dec-5-6/requirements/gqaNXa1D-design.md`, `gqaNXa1D-spec.md`, `gqaNXa1D-risks.md`
- `step-1-schedule-updates-cvrc-dec-5-6/step-outputs/gqaNXa1D-output-notes.md`, `gqaNXa1D-request.md`, `gqaNXa1D-handoff.md`, `xa6BE0FD-output-notes.md`
- `deploy/README.md`, `deploy/deploy.env.example`, `deploy/deploy.py` (deploy set, plan, remote listing, execute_plan), `deploy/tests/test_deploy.py` (dotfile tests)
- External: DNS/whois for both domains; HTTP and HTTPS probes of the live site; FatCow help (redirects to Network Solutions); webhostingplanguide.com FatCow SSL page; web search on FatCow free SSL and on proxy-safe HTTPS redirects.
- Skipped: `step-0-…/requirements/6PnyeVnB-spec.md` and `6PnyeVnB-risks.md` (the design covers what this step needs); `step-0-…/step-outputs/F6QxhKE1-*` and `*-request.md` (output notes read instead); `step-1-…/step-outputs/PK4mjlPv-*`, `x7Fg5RiT-*`, `xa6BE0FD-handoff.md` (content tasks unrelated to hosting); `deploy/preview.sh` (unchanged by this step).

## Not done / for the reviewer
- Nothing in the hosting panel can be checked from here; the FatCow identification and the free-vs-paid answer are John's at the review and certificate gates.
- The pre-existing `[needs-you] Confirm the hosting provider…` item sits after the merge/try item; see the design § Open decisions.
