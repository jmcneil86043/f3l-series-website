# Design — Step 2: Get a certificate and serve the site over HTTPS

Step: https://trello.com/c/RbsRQzYp   Written: 2026-09-24 by task 6ab523bfa0e4fe24df0a8d48
Spec: `step-2-get-a-certificate-and-serve-the/requirements/IVs7c008-spec.md`
Ledger: `decisions/F3L-Series-Web-Site-decisions.md`

## Summary

Two halves, in this order:

1. **Certificate (John, in the hosting panel).** The host is FatCow (Newfold). Its front end already terminates TLS for the site's address (port 443 answers with the site's pages behind a `*.bizland.com` wildcard), so nothing has to be installed by hand: the per-domain certificate is switched on in the control panel and the platform renews it. Route A below. If the panel only sells certificates, route B (buy the host's certificate) is the fallback; both are decided at the certificate gate.
2. **Site side (workers, deployed with Step 0).** A tracked `.htaccess` at the repo root redirects plain HTTP and the bare domain to `https://www.f3lcontestseries.org/…`; the footer self-link on all eight pages becomes `https://`; `deploy/deploy.py` learns to publish that one dotfile, uploading it last. Nothing is uploaded until the certificate is verified live; the closing task checks the certificate, publishes, and verifies the redirects.

No DNS change, no CDN, no HSTS, no canonical tags (spec § Assumptions).

## Facts gathered (2026-09-24, from this machine)

| Probe | Result |
|---|---|
| DNS | `www.f3lcontestseries.org` → CNAME `f3lcontestseries.org` → A `65.254.248.183`; `ftp.mcneilco.com` and `mcneilco.com` → A `65.254.248.220`. Both in Newfold's `65.254.248.0/24`. Name servers `ns-cloud-d{1..4}.googledomains.com`; registrar Squarespace Domains; expiry 2028-07-02. |
| FTP banner | `220 fatcow FTP Server Ready` (matches Step 0's finding: FatCow ProFTPD, plain FTP only). |
| HTTP | `http://www.…/` and `http://f3lcontestseries.org/` both 200, Apache-style `ETag`/`Last-Modified`, plus `X-Request-ID` and a `request_id` cookie from Newfold's front proxy. `Cache-Control: max-age=3600`. |
| `.htaccess` | `GET /.htaccess` → 403 (Apache's `.ht*` deny), so `.htaccess` is honoured on this platform, as FatCow documents. |
| HTTPS today | Port 443 on `65.254.248.183` answers with the site's own `index.html` (200 with `curl -k`) but presents `CN=*.bizland.com`, SANs `*.bizland.com, bizland.com`, DigiCert RapidSSL, valid 2026-08-12 → 2027-02-26. Browsers refuse it (name mismatch). Same wildcard on `www.mcneilco.com`. |
| ACME path | `GET /.well-known/acme-challenge/test` → plain 404 (no interception), so an HTTP-01 challenge file could be served if route B2 were ever needed. |
| FatCow docs | Free SSL is enabled per domain in the panel and covers the domain and its subdomains; it cannot be combined with a paid certificate on the same domain. The help site now redirects to `networksolutions.com/help`, so the panel may carry either brand. Panel is vDeck (FatCow's own; looks like cPanel, is not). Paid alternative historically ~$45/yr (GeoTrust/Comodo via the panel). |
| Site self-references | Exactly one per page: the footer `<a href="http://www.f3lcontestseries.org">` on all 8 pages. No `<link rel="canonical">`, no `og:url`, no `<base>`. No `http://` in any `src`, so no mixed content once HTTPS is on. `results.html` already frames F3XVault over https. One external `http://www.soarabq.org/` link (index, schedule) is out of scope. |
| Deploy tooling | `deploy.py` excludes every dotfile from the deploy set (`is_deploy_path`) and from remote-only reporting/deletion (`is_managed_remote_path`), so today `.htaccess` is neither uploaded nor ever deleted. The server manifest exists (deployed 2026-09-21 by `jam@Mika`), so Step 0's first live run has happened and deploys are incremental. |

The `*.bizland.com` wildcard on the site's own IP is the significant fact: it is Newfold's shared SSL front end. Enabling a domain certificate there is a panel action that provisions and renews on the platform; there is no server we configure.

## Certificate

### Route A — free certificate from the panel (expected)

John, at the certificate gate:

1. Sign in to the hosting control panel for the `mcneilco.com` account (FatCow vDeck, or its Network Solutions successor).
2. Find the SSL page. Likely names: **Security → SSL Certificates**, **Free SSL**, **SSL Manager**, or "Manage SSL" beside the domain in the domains list. `f3lcontestseries.org` is an add-on/pointed domain mapped to `/f3l_series`; pick that domain, not `mcneilco.com`.
3. Enable the free certificate for `f3lcontestseries.org`. FatCow's docs say it covers the domain and its subdomains, so `www` is included; if the panel asks, select both.
4. Wait for issuance (minutes to an hour), then check from any terminal, without `-k`:

   ```sh
   curl -sSI https://www.f3lcontestseries.org/ | head -1        # HTTP/1.1 200 OK, no certificate error
   curl -sSI https://f3lcontestseries.org/ | head -1            # same (bare domain)
   echo | openssl s_client -connect www.f3lcontestseries.org:443 -servername www.f3lcontestseries.org 2>/dev/null \
     | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
   ```

   Expected: subject/SAN naming `f3lcontestseries.org` and `www.f3lcontestseries.org`, issuer Let's Encrypt (or whatever CA the panel uses), not `*.bizland.com`.
5. Note, for the ledger: the panel page's name, whether it shows an expiry or a "renews automatically" statement, and whether an email address receives renewal notices. If the panel shows a **Force HTTPS** / "Redirect to HTTPS" toggle, leave it **off**: the redirect comes from the repo (§ Redirect) so it is versioned and testable; turning both on is harmless but pointless.

Renewal: Newfold-issued free certificates are 90-day certificates renewed by the platform. The gate confirms the panel says so; if it instead shows a manual "renew" action, that is recorded and the ledger entry says when the next renewal is due.

### Route B — the panel offers no free certificate

Decided at the same gate, in this order of preference:

- **B1 · Buy the host's certificate** for `f3lcontestseries.org` in the panel (historically ~$45/yr). The panel installs and renews it; everything else in this design is unchanged. Recommended fallback.
- **B2 · Self-issued Let's Encrypt** (certbot on the Mac, HTTP-01 challenge uploaded to `/.well-known/acme-challenge/` over FTP, then paste certificate and key into the panel's "install third-party certificate" page). Works on this host (§ Facts, ACME path) but must be repeated by hand every ≤ 90 days and puts a private key through the panel by hand. Only if B1 is unavailable and John accepts the chore.
- **B3 · Cloudflare (or similar) in front** gives free edge TLS but moves DNS off Google Cloud DNS and changes how the site is served. Out of scope here; it would be its own step with its own ledger entry.

Whichever route: the private key never enters the repo, and no credential from the panel is written anywhere but 1Password.

## Redirect

New tracked file `.htaccess` at the repo root, published to `/f3l_series/.htaccess`:

```apache
# HTTPS on the canonical host. Deployed by deploy/deploy.py; see deploy/README.md.
RewriteEngine On

# 1. Bare domain -> www (either scheme).
RewriteCond %{HTTP_HOST} ^f3lcontestseries\.org$ [NC]
RewriteRule ^ https://www.f3lcontestseries.org%{REQUEST_URI} [R=301,L]

# 2. Plain HTTP -> HTTPS. Both conditions must hold, so this cannot loop
#    whether the front end reports TLS through HTTPS or X-Forwarded-Proto.
RewriteCond %{HTTPS} !=on
RewriteCond %{HTTP:X-Forwarded-Proto} !=https
RewriteRule ^ https://www.f3lcontestseries.org%{REQUEST_URI} [R=301,L]
```

Why this shape:
- Newfold sites sit behind a proxy (the `X-Request-ID` header). On such hosts `%{HTTPS}` is sometimes `off` for TLS requests and only `X-Forwarded-Proto: https` tells the truth. Requiring **both** to say "not HTTPS" before redirecting means a TLS request is never redirected again, whichever variable the platform sets. The only failure mode is "neither is set for a TLS request", which the closing task's curl checks would show as a 301-to-self, with the rollback below.
- `%{REQUEST_URI}` keeps the path and query, so deep links and the manifest URL survive.
- 301 (permanent) is what search engines and browsers should learn. Browsers cache 301s, so the closing task tests with curl, not a browser, and rollback (below) may leave a tester's browser redirecting until its cache clears.
- Rule 1 makes `https://www.…` the single canonical form (spec § Assumptions). Strike it at review to leave the bare domain as a second HTTPS name.
- No HSTS. Add `Header always set Strict-Transport-Security "max-age=…"` in a later step once HTTPS has run cleanly.

`.htaccess` cannot be previewed by `deploy/preview.sh` (Python's `http.server` ignores it); it is only testable live, which is why the closing task publishes and checks in one run.

**Rollback** (from any checkout with credentials): comment out both rules, commit, `deploy/deploy.py --upload`. The file changes hash, so it is re-sent; `--delete` is never involved (it never touches dotfiles).

## Site-side link changes

- On all eight pages (`index`, `schedule`, `results`, `postal`, `about`, `howto`, `host`, `highstart`), the footer `href="http://www.f3lcontestseries.org"` becomes `href="https://www.f3lcontestseries.org/"`. Nothing else in the pages references the site's own address.
- `README.txt`: add `.htaccess` to the structure listing with a one-line note that it is the HTTPS redirect.
- `deploy/README.md`: the manifest example `curl` uses `https://`; "What gets published" gains `.htaccess` at the repo root; the `--delete` note ("never dotfiles such as `.htaccess`") stays true and is kept.

## Deploy tooling change (`deploy/deploy.py`)

Minimal, explicit, in the existing style:

- New constant next to `DEPLOY_STYLESHEET`: `DEPLOY_ROOT_DOTFILES = (".htaccess",)` with a comment that these are the only dotfiles ever published.
- `is_deploy_path(rel)`: return `True` when `rel` is exactly one of `DEPLOY_ROOT_DOTFILES` (root only; `assets/.htaccess` and `.htaccess.bak` stay excluded), checked before the general dotfile exclusion. `collect_deploy_set` needs no change: it only prunes dot-*directories* and already routes files through `is_deploy_path`.
- `upload_order(rel)`: `.htaccess` sorts **after** pages (`(3, rel)`), so the redirect is the last thing to go live in a run; assets → stylesheet → pages → `.htaccess`. Update the comment on `Plan.to_upload`.
- `is_managed_remote_path` unchanged: a remote `.htaccess` the repo does not have is still neither reported nor deleted, and a `.htaccess` the repo does have is in `local`, so it is classified new/changed/unchanged like any file.
- Tests in `deploy/tests/test_deploy.py`: `is_deploy_path(".htaccess")` true; `"assets/.htaccess"`, `".htaccess.bak"`, `".f3l-deploy-manifest.json"` false; `collect_deploy_set` on a temp tree with a root `.htaccess` includes it (extend `test_excludes_non_site_files_and_dotfiles`: add `.htaccess` to the written files and expect 7, and assert it is present); `upload_order` places `.htaccess` after `index.html`; execute_plan uploads it last (FakeRemote log order). Remote-only test with a server-side `.htaccess` and no local one still excludes it.

No change to credentials, manifest format, FTP code or the CLI. `deploy/README.md` documents the one exception to the dotfile rule.

## Verification and publish (closing task)

Runs on a machine with `~/.config/f3l-series-website/deploy.env` (Bishop or John's Mac). In order:

1. **Certificate live?** `curl -sSI https://www.f3lcontestseries.org/` (no `-k`) must return 200 and `openssl x509` must show the site's name in the SAN list. If not, stop **blocked** with the openssl output in the hand-off; do not upload. This is the guard that keeps the redirect from going live before the certificate.
2. `python3 -m unittest discover -s deploy/tests` → OK.
3. `deploy/deploy.py` dry run: expect `.htaccess` new, 8 pages changed, nothing else; record the plan.
4. Commit anything outstanding, then `deploy/deploy.py --upload`.
5. Live checks, all with curl (`-sSI`, `-o /dev/null -w '%{http_code} %{redirect_url}\n'`):
   - `http://www.f3lcontestseries.org/` → 301 → `https://www.f3lcontestseries.org/`
   - `http://www.f3lcontestseries.org/schedule.html` → 301 → `https://www.f3lcontestseries.org/schedule.html` (path preserved)
   - `http://f3lcontestseries.org/` and `https://f3lcontestseries.org/postal.html` → 301 → the `www` https form
   - `https://www.f3lcontestseries.org/` → 200 with **no** `Location` header (no loop); `curl -L --max-redirs 3` on the http form lands on 200.
   - every page over https → 200; `grep -c 'http://' ` on each fetched page finds only the external soarabq link and the w3.org SVG namespace.
   - `https://www.f3lcontestseries.org/.f3l-deploy-manifest.json` shows the step's final commit.
6. If step 5 shows a redirect loop or any non-200 page: roll back per § Redirect (comment the rules out, commit, `--upload`), re-check, and stop **blocked** with the curl output.
7. A second dry run reports nothing to send.
8. Ledger: two lines under "Repo and runtime": the certificate route actually taken and where it renews (from the gate's comment), and "the site's only server configuration is the tracked `.htaccess`, published by `deploy.py` as the one dotfile in the deploy set". Output notes, commit.

## Files

| Path | Status | Change |
|---|---|---|
| `.htaccess` | new | the two redirect rules |
| `index.html`, `schedule.html`, `results.html`, `postal.html`, `about.html`, `howto.html`, `host.html`, `highstart.html` | edit | footer self-link → `https://…/` |
| `README.txt` | edit | `.htaccess` in the structure list |
| `deploy/deploy.py` | edit | `DEPLOY_ROOT_DOTFILES`, `is_deploy_path`, `upload_order` |
| `deploy/tests/test_deploy.py` | edit | the tests listed above |
| `deploy/README.md` | edit | the dotfile exception, https manifest URL, upload order |
| `decisions/F3L-Series-Web-Site-decisions.md` | edit | two lines (closing task) |

`styles.css`, `assets/`, `deploy/preview.sh`, credentials: untouched.

## Implementation tasks

1. **Teach `deploy.py` to publish a root `.htaccess`** — `DEPLOY_ROOT_DOTFILES`, `is_deploy_path`, `upload_order` last, the tests in § Deploy tooling change, `deploy/README.md` wording. Run the suite, commit. Size: 3 files, ~15 min.
2. **Add `.htaccess`, switch the footer self-link on all 8 pages, `README.txt` line** — the file from § Redirect verbatim; `sed`-style edit of the one footer href per page; dry run to confirm the plan is `.htaccess` new + 8 changed; commit. **No `--upload`.** Size: 10 files, ~15 min.
3. **`[needs-you]` Certificate gate** — John enables the certificate per § Certificate (route A, else B1) and confirms with the curl/openssl checks; his comment on the gate's task card records the panel page name and the renewal statement for the ledger.
4. **Closing: verify certificate, publish, verify redirects, ledger, notes** — § Verification and publish, steps 1–8. Stops blocked without uploading if the certificate is not live. Size: 2 files (ledger, notes) plus the upload, ~15 min.

Checklist names as they should appear on the step card, after this task's item:
1. `[needs-you] Review the design and plan`
2. `Teach deploy/deploy.py to publish a root .htaccess (deploy set, uploaded last, tests, deploy/README.md)`
3. `Add .htaccess with the HTTPS and www redirect, switch the footer self-link on all 8 pages to https://, add the README.txt line; dry run and commit, no upload`
4. `[needs-you] Enable the certificate for f3lcontestseries.org in the hosting control panel (design § Certificate, route A else B1) and confirm https://www.f3lcontestseries.org/ loads with no warning`
5. `Closing: confirm the certificate is live, run tests and dry run, publish with deploy.py --upload, verify the redirects and every page over HTTPS, ledger lines, notes, commit`
6. `[needs-you] Merge the branch into main (task-dispatcher merge-step RbsRQzYp), then try the new functions yourself`

The pre-existing item `Confirm the hosting provider and control-panel access … note which certificate options it offers [needs-you]` cannot be moved by this task, so it will sit **after** item 6. Its substance is answered by the review (item 1, where John confirms the FatCow identification) and item 4 (where the option offered is used). John can tick it at either point; see § Open decisions.

## Runner impact

(none — no task touches task-dispatcher, trello-automation or any MCP server; only site files, `deploy/`, docs and the ledger.)

## Open decisions

- **Checklist order.** The pre-existing `[needs-you] Confirm the hosting provider…` item lands after the merge/try item because existing items are never reordered. The certificate gate (item 4) is where that confirmation is actually used. Either tick the old item when you do item 4, or move it yourself; the design assumes nothing about its position.
- **Who runs `--upload`.** The closing worker publishes, because it verifies the certificate and the redirects in the same run. Say at review if you would rather run `deploy/deploy.py --upload` yourself in the try item; then task 4 stops after its dry run and the try item's checklist carries § Verification steps 5–7.
- **Bare domain → www (rule 1).** Included so there is one canonical HTTPS address. Strike it if you want `https://f3lcontestseries.org/` to serve directly (the free certificate should cover both names either way).
- **Panel "Force HTTPS" toggle.** If the panel offers one, the design leaves it off and uses the repo's `.htaccess`. Say if you prefer the toggle; then task 2 ships no `.htaccess` and task 1 is unnecessary.
- **Canonical tags and HSTS.** Neither is added (spec § Assumptions). Say if you want `<link rel="canonical">` on each page (one line per page, task 2) or a short-max-age HSTS header (one line in `.htaccess`).
