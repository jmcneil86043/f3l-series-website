# Risks — Step 2: Get a certificate and serve the site over HTTPS

Step: https://trello.com/c/RbsRQzYp   Written: 2026-09-24 by task 6ab523bfa0e4fe24df0a8d48
Design: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-design.md`

## What breaks while this change is in flight
(none)

## What could go wrong with this change
- **Redirect published before the certificate is live** · likelihood low · impact high · noticed by: every http visitor lands on a certificate warning; the closing task's step-1 check fails · mitigation/rollback: tasks 1–2 never upload; the closing task refuses to upload unless `curl https://…` succeeds without `-k`; if it ever happens, comment out the rules, commit, `--upload` (about a minute).
- **Redirect loop on the proxy** (neither `HTTPS` nor `X-Forwarded-Proto` reports TLS) · likelihood low · impact high · noticed by: `curl -sSI https://www…/` returns 301 to itself; browsers show "too many redirects" · mitigation/rollback: the two-condition rule makes this unlikely; the closing task checks with curl straight after upload and rolls back the same way as above. Browsers may keep a cached 301 for a while afterwards.
- **Certificate covers only one of www / bare domain** · likelihood low · impact medium · noticed by: the gate's second curl (bare domain) fails while the first passes · mitigation/rollback: rule 1 already sends the bare domain to www over https, so a www-only certificate still works for anyone who types the bare name over http; https on the bare name would fail as it does today. Re-enable in the panel selecting both names.
- **Renewal is not automatic after all** · likelihood low · impact high (site breaks ~90 days later) · noticed by: the panel shows a manual "renew" action or an expiry date without "auto"; later, browser warnings · mitigation/rollback: the gate records the renewal statement; if manual, the ledger line carries the due date and John gets a Trello card to renew; the redirect can be commented out in an emergency so http keeps working.
- **`.htaccess` syntax rejected by the host** (500 on every page) · likelihood low · impact high · noticed by: the closing task's page sweep returns 500s · mitigation/rollback: same rollback (comment out, commit, `--upload`); `.htaccess` uploads last in a run, so pages and assets are already consistent when it lands.
- **Old browser-cached 301s during a rollback** · likelihood medium (only if a rollback happens) · impact low · noticed by: John's browser still redirecting after the file is reverted · mitigation/rollback: test with curl; clear the site's cached redirects or wait.
- **Deploy tooling change publishes something unintended** · likelihood low · impact low · noticed by: the dry run in task 2 lists more than `.htaccess` + 8 pages · mitigation/rollback: the include is an exact-name tuple at the root; the test suite pins the exclusions; fix and re-run before any upload.
- **The manifest URL or other docs still say http** · likelihood low · impact low · noticed by: a curl in the README following a 301 · mitigation/rollback: docs edit, no deploy needed.
