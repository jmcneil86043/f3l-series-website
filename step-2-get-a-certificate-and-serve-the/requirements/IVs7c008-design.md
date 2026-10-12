# Design — Step 2: Get a certificate and serve the site over HTTPS

Step: https://trello.com/c/RbsRQzYp   Written: 2026-09-24 by task 6ab523bfa0e4fe24df0a8d48   Reviewed: 2026-10-12 (rulings in § Decisions at review)
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
| Co-hosting (added at review, 2026-10-12) | The site is a subdirectory of the `www.mcneilco.com` document root: `http://www.mcneilco.com/f3l_series/` serves the F3L home page (`65.254.248.220`, title "F3L Contest Series - Home"). So `/f3l_series/.htaccess` is reached through **two** hosts: the F3L vhost (where `REQUEST_URI` is `/schedule.html`) and the mcneilco.com vhost (where it is `/f3l_series/schedule.html`). The mcneilco.com pages themselves are above that directory and are not governed by the file. `www.mcneilco.com` shows the same `*.bizland.com` wildcard on 443, no `http://` references on its home page, and its own site is not in this repo (source `~/Projects/JMCo/mcneilco.com`, last published 2018). |
| Front cache (added at review, 2026-10-12) | Both hosts answer with `Cache-Control: max-age=3600` and an `Age:` header from Newfold's front proxy, so a freshly uploaded redirect can be masked by a cached 200 for up to an hour. |

The `*.bizland.com` wildcard on the site's own IP is the significant fact: it is Newfold's shared SSL front end. Enabling a domain certificate there is a panel action that provisions and renews on the platform; there is no server we configure.

## Certificate

### Route A — free certificate from the panel (expected)

John, at the certificate gate:

1. Sign in to the hosting control panel for the `mcneilco.com` account. Per John's Bear note "setting up web hosting on fatcow" (2026-02-13, `#TPG/F3LSeries`), FatCow is now **iPage**: the login is `https://secure.ipage.com/secure/login.html`, 1Password item `IPage` (vault `Personal`, user `jmcneil`). iPage is the same Newfold vDeck panel; an older `secure.fatcow.com` keychain item also exists. The note also records that `f3lcontestseries.org` was added as a pointed domain (Domain settings → Pointer & Subdomains) mapped to the `F3l_series` folder without transferring registration.
2. Find the SSL page. Likely names: **Security → SSL Certificates**, **Free SSL**, **SSL Manager**, or "Manage SSL" beside the domain in the domains list. `f3lcontestseries.org` is an add-on/pointed domain mapped to `/f3l_series`; pick that domain, not `mcneilco.com`.
3. Enable the free certificate for `f3lcontestseries.org`. FatCow's docs say it covers the domain and its subdomains, so `www` is included; if the panel asks, select both.
   While on the same page, enable the free certificate for `mcneilco.com` as well (ruling of 2026-10-12). It is additive: plain HTTP on mcneilco.com keeps working exactly as today and nothing in this repo redirects that site. Do **not** switch on any "Force HTTPS" toggle for either domain; on a co-hosted account such a toggle may be account-wide. The mcneilco.com redirect and link work is a separate piece of work outside this repo.
4. Wait for issuance (minutes to an hour), then check from any terminal, without `-k`:

   ```sh
   curl -sSI https://www.f3lcontestseries.org/ | head -1        # HTTP/1.1 200 OK, no certificate error
   curl -sSI https://f3lcontestseries.org/ | head -1            # same (bare domain)
   echo | openssl s_client -connect www.f3lcontestseries.org:443 -servername www.f3lcontestseries.org 2>/dev/null \
     | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
   ```

   Expected: subject/SAN naming `f3lcontestseries.org` and `www.f3lcontestseries.org`, issuer Let's Encrypt (or whatever CA the panel uses), not `*.bizland.com`. Run the first `curl` line against `https://www.mcneilco.com/` too and expect the same.
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
# This directory is also reachable as www.mcneilco.com/f3l_series/, so every
# rule is scoped by host; nothing here may touch the mcneilco.com site.
RewriteEngine On

# 1. Bare domain -> www (either scheme).
RewriteCond %{HTTP_HOST} ^f3lcontestseries\.org$ [NC]
RewriteRule ^ https://www.f3lcontestseries.org%{REQUEST_URI} [R=301,L]

# 2. Plain HTTP -> HTTPS, on the site's own host only. Both TLS conditions
#    must hold, so this cannot loop whether the front end reports TLS
#    through HTTPS or X-Forwarded-Proto.
RewriteCond %{HTTP_HOST} ^(www\.)?f3lcontestseries\.org$ [NC]
RewriteCond %{HTTPS} !=on
RewriteCond %{HTTP:X-Forwarded-Proto} !=https
RewriteRule ^ https://www.f3lcontestseries.org%{REQUEST_URI} [R=301,L]

# 3. The co-hosted path www.mcneilco.com/f3l_series/... -> the canonical site.
#    Per-directory rewriting strips the directory prefix, so $1 is the path
#    relative to this folder; the query string is passed through by default.
RewriteCond %{HTTP_HOST} ^(www\.)?mcneilco\.com$ [NC]
RewriteRule ^(.*)$ https://www.f3lcontestseries.org/$1 [R=301,L]
```

Why this shape:
- **Every rule carries a host condition** (ruling of 2026-10-12). Without one on rule 2, a visitor at `http://www.mcneilco.com/f3l_series/x` would be sent to `https://www.f3lcontestseries.org/f3l_series/x`, a 404, because `REQUEST_URI` there carries the `/f3l_series` prefix. Rule 3 handles that path on purpose instead, with the prefix stripped. Any other host that reaches this directory falls through untouched.
- Newfold sites sit behind a proxy (the `X-Request-ID` header). On such hosts `%{HTTPS}` is sometimes `off` for TLS requests and only `X-Forwarded-Proto: https` tells the truth. Requiring **both** to say "not HTTPS" before redirecting means a TLS request is never redirected again, whichever variable the platform sets. The only failure mode is "neither is set for a TLS request", which the closing task's curl checks would show as a 301-to-self, with the rollback below.
- `%{REQUEST_URI}` keeps the path and query, so deep links and the manifest URL survive.
- 301 (permanent) is what search engines and browsers should learn. Browsers cache 301s, so the closing task tests with curl, not a browser, and rollback (below) may leave a tester's browser redirecting until its cache clears.
- Rule 1 makes `https://www.…` the single canonical form (spec § Assumptions). Strike it at review to leave the bare domain as a second HTTPS name.
- No HSTS. Add `Header always set Strict-Transport-Security "max-age=…"` in a later step once HTTPS has run cleanly.
- `RewriteEngine On` in this directory stops any rewrite rules in a parent `.htaccess` (the account root, which is the mcneilco.com document root) from applying to F3L requests; mod_rewrite does not inherit by default. Nothing is known to be there. The closing task reads the account root over FTP before publishing (§ Verification, step 1) and, if a root `.htaccess` with `RewriteRule` lines exists, adds `RewriteOptions Inherit` under `RewriteEngine On` so those rules keep running after ours.

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
   **Account root `.htaccess`?** Over the same FTP credentials, list the directory one level above the remote dir (the account root, which is the mcneilco.com document root; `ftplib` `MLSD` or `NLST` on `/`). Read only. If it holds a `.htaccess`, download it to a scratch location (never into the repo) and read it: if it contains `RewriteRule` lines, add `RewriteOptions Inherit` to the repo's `.htaccess` directly under `RewriteEngine On` and commit before step 2; record what was found in the output notes either way.
2. `python3 -m unittest discover -s deploy/tests` → OK.
3. `deploy/deploy.py` dry run: expect `.htaccess` new, 8 pages changed, nothing else; record the plan.
4. Commit anything outstanding, then `deploy/deploy.py --upload`.
5. Live checks, all with curl (`-sSI`, `-o /dev/null -w '%{http_code} %{redirect_url}\n'`). **The front proxy caches for an hour** (§ Facts), so append a cache-busting query string that changes per attempt (for example `?v=<commit>-<attempt>`) to every URL below; the redirect rules pass the query string through, so the expected `Location` carries it too. A 200 from an un-busted URL within the hour after upload is a stale cache hit, not a failure.
   - `http://www.f3lcontestseries.org/` → 301 → `https://www.f3lcontestseries.org/`
   - `http://www.f3lcontestseries.org/schedule.html` → 301 → `https://www.f3lcontestseries.org/schedule.html` (path preserved)
   - `http://f3lcontestseries.org/` and `https://f3lcontestseries.org/postal.html` → 301 → the `www` https form
   - `https://www.f3lcontestseries.org/` → 200 with **no** `Location` header (no loop); `curl -L --max-redirs 3` on the http form lands on 200.
   - every page over https → 200; `grep -c 'http://' ` on each fetched page finds only the external soarabq link and the w3.org SVG namespace.
   - `https://www.f3lcontestseries.org/.f3l-deploy-manifest.json` shows the step's final commit.
   - **mcneilco.com untouched:** `http://www.mcneilco.com/` and `http://mcneilco.com/` → 200, no `Location`, title still "John McNeil and Co., Inc."; `http://www.mcneilco.com/acas.html` → 200.
   - **co-hosted path:** `http://www.mcneilco.com/f3l_series/` → 301 → `https://www.f3lcontestseries.org/` and `http://www.mcneilco.com/f3l_series/schedule.html` → 301 → `https://www.f3lcontestseries.org/schedule.html` (prefix stripped, not duplicated).
6. If step 5 shows a redirect loop, a 500, any non-200 page, or **any change to the mcneilco.com responses**: roll back per § Redirect (comment the rules out, commit, `--upload`), re-check with fresh cache-busters, and stop **blocked** with the curl output. Do not roll back on a plain 200 from a URL without a cache-buster.
7. A second dry run reports nothing to send.
8. Ledger: two lines under "Repo and runtime": the certificate route actually taken and where it renews (from the gate's comment), and "the site's only server configuration is the tracked `.htaccess`, published by `deploy.py` as the one dotfile in the deploy set". Output notes, commit.

## Files

| Path | Status | Change |
|---|---|---|
| `.htaccess` | new | the three host-scoped redirect rules |
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
3. **`[needs-you]` Certificate gate** — John enables the certificate for `f3lcontestseries.org` and, on the same visit, for `mcneilco.com`, per § Certificate (route A, else B1), and confirms with the curl/openssl checks; his comment on the gate's task card records the panel page name and the renewal statement for the ledger.
4. **Closing: verify certificate, read the account root, publish, verify redirects and mcneilco.com, ledger, notes** — § Verification and publish, steps 1–8. Stops blocked without uploading if the certificate is not live. Size: 2 files (ledger, notes), possibly one `RewriteOptions Inherit` line, plus the upload, ~20 min.

Checklist names as they should appear on the step card, after this task's item:
1. `[needs-you] Review the design and plan`
2. `Teach deploy/deploy.py to publish a root .htaccess (deploy set, uploaded last, tests, deploy/README.md)`
3. `Add .htaccess with the HTTPS and www redirect, switch the footer self-link on all 8 pages to https://, add the README.txt line; dry run and commit, no upload`
4. `[needs-you] Enable the free certificate for f3lcontestseries.org and for mcneilco.com in the hosting control panel (design § Certificate, route A else B1; no Force-HTTPS toggle) and confirm https://www.f3lcontestseries.org/ loads with no warning`
5. `Closing: confirm the certificate is live, run tests and dry run, publish with deploy.py --upload, verify the redirects and every page over HTTPS, ledger lines, notes, commit` (the mcneilco.com checks and the cache-busting are in the design § Verification; the item name was left as is)
6. `[needs-you] Merge the branch into main (task-dispatcher merge-step RbsRQzYp), then try the new functions yourself`

The pre-existing item `Confirm the hosting provider and control-panel access … note which certificate options it offers [needs-you]` cannot be moved by this task, so it will sit **after** item 6. Its substance is answered by the review (item 1, where John confirms the FatCow identification) and item 4 (where the option offered is used). John can tick it at either point; see § Open decisions.

## Runner impact

(none — no task touches task-dispatcher, trello-automation or any MCP server; only site files, `deploy/`, docs and the ledger.)

## Decisions at review (2026-10-12)

John reviewed the design on 2026-10-12 and approved it with the changes now folded into the sections above. No open decisions remain.

- **Co-hosting constraint (new).** `www.mcneilco.com` is served from the parent of this site's directory and must not break. Every redirect rule is scoped by host, the co-hosted `/f3l_series/` path redirects to the canonical site with its prefix stripped (rule 3), and the closing task checks mcneilco.com's own responses before and after the publish and rolls back on any change to them.
- **Same upgrade for mcneilco.com.** The free certificate is enabled for `mcneilco.com` at the same panel visit as the F3L one (additive, HTTP unaffected). Its own HTTPS redirect and link changes are outside this repo and this step; they are separate work.
- **Front cache.** Live checks use cache-busting query strings and never treat a stale cached 200 as a failure.
- **Parent `.htaccess`.** The closing task reads the account root over FTP first and adds `RewriteOptions Inherit` only if a root `.htaccess` has rewrite rules.
- **Checklist order.** The pre-existing `[needs-you] Confirm the hosting provider…` item stays after the merge/try item; John ticks it when he does the certificate gate.
- **Who runs `--upload`.** The closing worker publishes, as designed.
- **Bare domain → www (rule 1).** Kept.
- **Panel "Force HTTPS" toggle.** Left off for both domains; the redirect lives in the repo.
- **Canonical tags and HSTS.** Neither in this step, as designed.
