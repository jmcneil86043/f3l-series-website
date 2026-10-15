# Hosting requirements — www.f3lcontestseries.org and www.mcneilco.com

Written 2026-10-15 for step "Select web hosting" (https://trello.com/c/DJy1ViGr), task R5S2o7dv.

This document is the input to the host comparison. It says what each site actually is today, what
the new hosting has to do, and what it must not do. It chooses no host and buys nothing.

---

## 1. Sources, and what was not reachable

**The 2026-10-13 FTP backup was not reachable from the machine that ran this step.** The step card
names it at `~/Projects/TPG/F3L Series/WebSite/ftp-backup-2026-10-13/` on **Mika**; this step ran on
**Bishop**, where neither that folder nor `~/Projects/TPG` exists. The static staging repo named in
the 2026-10-15 card comment, `~/Projects/JMCo/mcneilco.com-site` on Mika, is likewise not on this
machine. Both were searched for before falling back.

As the card directs, the inventory below therefore comes from **this repo and the live sites**:

| Source | Used for | Read |
|---|---|---|
| This worktree (`step/DJy1ViGr-select-web-hosting`) | The complete F3L inventory | 2026-10-15 |
| `http://www.f3lcontestseries.org/` (live) | Confirming the repo matches what is served | 2026-10-15 |
| `http://www.mcneilco.com/` (live, crawled) | The whole mcneilco.com inventory | 2026-10-15 |
| `dig` against 8.8.8.8 and 1.1.1.1 | Every DNS and mail fact in §6 and §7 | 2026-10-15 |
| TLS handshake against both hosts (`curl -v`) | The certificate facts in §5.3 | 2026-10-15 |

**What this fallback costs.** Two gaps follow from not having the backup, and both matter to the
next step:

- The mcneilco.com figures in §3 are **crawl-derived**: they cover every file reachable by following
  links from the live pages. They total **131 files / 48.5 MB**, against the **177 files / 71 MB**
  the card reports for the staging repo. The difference — roughly 46 files and 22 MB — is files the
  live pages do not link to, which a crawl cannot see. Treat the staging repo as authoritative for
  the migration payload and these numbers as a verified floor.
- Nothing here can confirm the card's statement that the root `.htaccess` is empty. The live server
  returns `403` for `/.htaccess` (as it should), so its contents could not be read. §5.4 records
  only the redirect behaviour that is externally observable.

Everything else below was measured directly, not copied from the card. Where a measurement
contradicts or adds to the card, it is called out.

---

## 2. Site A — www.f3lcontestseries.org

### 2.1 Provenance

This repo is the source of truth. Spot checks against the live site match byte for byte:

| File | Live | Repo |
|---|---|---|
| `index.html` | 6,469 | 6,469 |
| `styles.css` | 9,096 | 9,096 |
| `about.html` | 9,039 | 9,039 |
| `host.html` | 20,079 | 20,079 |
| `assets/F3L contest bulletin template 2026 v1.1.doc` | 56,320 | 56,320 |

### 2.2 What gets published

The published set is defined in code, by `is_deploy_path()` in `deploy/deploy.py`: top-level
`*.html`, plus `styles.css`, plus everything under `assets/`. Dotfiles and every other directory
(`deploy/`, `decisions/`, the step folders, `README.txt`) are excluded. Computed with that function
on 2026-10-15:

**31 files, 35,018,920 bytes (33.4 MB).**

| Type | Files | Bytes | |
|---|---:|---:|---|
| `.jpg` | 15 | 22,569,261 | 21.52 MB |
| `.png` | 4 | 7,118,764 | 6.79 MB |
| `.jpeg` | 2 | 5,182,541 | 4.94 MB |
| `.html` | 8 | 82,938 | 0.08 MB |
| `.doc` | 1 | 56,320 | 0.05 MB |
| `.css` | 1 | 9,096 | 0.01 MB |

**Pages (8):** `index.html`, `about.html`, `schedule.html`, `results.html`, `postal.html`,
`howto.html`, `host.html`, `highstart.html`. One stylesheet, `styles.css`.

**Assets:** 14 files directly in `assets/` (32.60 MB) and 8 in `assets/highstart/` (0.71 MB).
Largest single files: `assets/wagon.jpg` 6.55 MB, `assets/ABQPilots.PNG` 6.19 MB,
`assets/flight_line.jpg` 4.02 MB, `assets/launch_1.jpeg` 3.94 MB, `assets/planes_1.jpg` 3.89 MB.

Note the payload is **99.6% unoptimised photography** (34.87 MB of 35.02 MB). Ten files account for over 32 of the 33.4 MB.
This is worth knowing for any host that bills by stored GB or by egress, and for any host with a
per-file or per-deploy size cap.

### 2.3 Dynamic bits

**None.** No `.php` file anywhere in the repo, no `<form>` on any page, no server-side include, no
build step. Two pages (`host.html`, `results.html`) carry a small inline `<script>` — in both cases
the same client-side `switchTab()` tab-switcher. Nothing is fetched or posted. The site is already
pure static vending and satisfies R1 (§8) as it stands.

### 2.4 External references

All internal links are **relative** — the site works from any document root, which is why it can sit
at `/f3l_series` today and at a bucket root tomorrow.

Outbound links point at 63 distinct external URLs across 26 hosts: RCGroups forum threads (the bulk of them),
F3XVault, FAI, club sites (Phoenix Model Glider Club, Torrey Pines Gulls, SoarABQ, CVRC, Silent
Flight), YouTube, a Zoom meeting link, and a dozen retailer links on `highstart.html`.

Two things here bear on the HTTPS migration:

- **`results.html` embeds two `<iframe>`s** from `https://www.f3xvault.com/` (the 2026 and 2025
  series standings). These are already HTTPS, so they will not break as mixed content — but they are
  a third-party embed, and a host that sets a restrictive `Content-Security-Policy` or
  `X-Frame-Options` by default must not break them.
- **The footer self-link on all 8 pages is `http://www.f3lcontestseries.org`**, plain HTTP. So are
  the two links to `http://www.soarabq.org/`. The footer links are navigation, not subresources, so
  they are not mixed-content blockers, but once the site is HTTPS they send visitors out through a
  cleartext redirect back to the site. They should be changed to `https://` as part of the cutover.

### 2.5 Downloads

One download, and it is the point of the `host.html` page: `assets/F3L contest bulletin template
2026 v1.1.doc` (56,320 bytes), linked with the HTML `download` attribute at `host.html:240`.

Two constraints follow. The filename **contains spaces**, and the host must serve it under that
exact name without mangling it. And a `.doc` must arrive as a **download, not a render or a
redirect** — any host that forces `Content-Disposition: inline` on unknown types, or rewrites the
name, fails here. One page also links out to a PDF on `fai.org`; that is not hosted here.

---

## 3. Site B — www.mcneilco.com

Crawled live on 2026-10-15 from `http://www.mcneilco.com/index.html`, following local links only,
then resolving the font and image URLs inside each stylesheet. The live host rejects unknown
user-agents with `HTTP 465`, so the crawl presented a browser user-agent.

### 3.1 Pages

| Page | Status | Bytes |
|---|---|---:|
| `index.html` | 200 | 6,947 |
| `acas.html` | 200 | 8,081 |
| `acas_docs.html` | 200 | 30,480 |
| `features.html` | 200 | 31,219 |
| `getacas.html` | 200 | 6,990 |
| `partners.html` | 200 | 5,080 |
| `sales.html` | 200 | 6,972 |
| `getstarted.php` | 200 | 7,063 |
| `contact_form.php` | 200 | 1,374 |
| `contact.php` | **409 Conflict** | — |

Seven HTML pages, 95,769 bytes. `acas_docs.html` and `sales.html` are not linked from any crawled
page and were fetched directly — they exist but are orphaned in the live link graph.

### 3.2 Dynamic bits — the only ones across both sites

Three PHP files, all of them the contact path:

- **`contact.php` returns `409 Conflict`.** The contact link on the live site is therefore already
  broken, exactly as the card says. Confirmed 2026-10-15.
- **`getstarted.php` returns 200** and serves ordinary HTML (`text/html; charset=UTF-8`). It works
  today; it is PHP only because it wraps a form.
- **`contact_form.php` returns 200** (1,374 bytes) but is linked from nothing.

Per the 2026-10-15 card comment these have already been resolved in the staging repo:
`contact.php` and `getstarted.php` became `contact.html` and `getstarted.html` with `mailto:`
links to sales@mcneilco.com, and `contact_form.php` was dropped as unlinked. **After that change
neither site has any server-side code**, and R1 (§8) is satisfiable without further work.

No other dynamic element exists: one JavaScript file (`js/bootstrap.min.js`), no server-side
includes, no database, no build step.

### 3.3 Files and sizes

**131 files, 50,844,120 bytes (48.5 MB) reachable by crawl.** See §1 for why this is a floor rather
than the full payload.

| Type | Files | Bytes | | Notes |
|---|---:|---:|---|---|
| Lato webfonts | 72 | 24,563,988 | 23.43 MB | `fonts/lato/`, 18 weights × eot/ttf/woff/woff2 |
| PDF | 4 | 15,980,254 | 15.24 MB | `tutorials/`, the product manuals |
| PNG + ICO | 28 | 8,859,506 | 8.45 MB | `assets/` (25), plus `GroupPhotoSwoop.png` 4.12 MB |
| Webfonts (other) | 10 | 944,428 | 0.90 MB | Font Awesome 4.5.0 + Bootstrap glyphicons |
| CSS | 7 | 354,922 | 0.34 MB | Bootstrap (full + min), Lato, Font Awesome, `mcneilco.css` |
| HTML | 7 | 95,769 | 0.09 MB | §3.1 |
| JS | 1 | 36,816 | 0.04 MB | `bootstrap.min.js` |
| PHP-served HTML | 2 | 8,437 | 0.01 MB | `getstarted.php`, `contact_form.php` |

Directory layout: `assets/`, `css/`, `fonts/font-awesome/`, `fonts/lato/`, `js/`, `tutorials/`,
plus loose files at the root (`index.html`, `mcneilco.css`, `ampersand.png`, `ampersand.ico`,
`GroupPhotoSwoop.png`).

Two observations for the comparison. **Half this site is webfonts** — 23.4 MB of Lato in four
formats across 18 weights, of which the pages use a handful. And the 72-file font directory plus
25-file asset directory make the **file count**, not the byte count, the thing a per-request-priced
or per-file-upload-limited host will notice.

### 3.4 Downloads

Four product-manual PDFs under `tutorials/`, 1.7–6.7 MB each, 15.24 MB total: `McNeilCoACAS.pdf`
(6.74 MB), `McNeilCoDoseResponse.pdf` (4.00 MB), `McNeilCoCompoundRegistration.pdf` (3.50 MB),
`McNeilCoPlateAnalysis.pdf` (1.74 MB). These are the site's reason for existing alongside the
product pages and must keep working, at their current paths.

### 3.5 Broken references that already exist

Three, all pre-existing. They are **not** regressions to be introduced by the migration, and the new
host must not be blamed for them — but they should be fixed during it, because a strict static host
will make them more visible than the current one does.

1. **`tutorials/McNeilCoDataViewer.pdf` → 404.** Linked from the docs page; the file is gone. Named
   in the staging repo README as a known gap.
2. **A schemeless `www.chemaxon.com` link**, which the browser resolves as a relative path and
   returns 404. Also named in the staging repo README.
3. **`css/latofonts.css` points at the wrong path.** It asks for `fonts/Lato-*.woff2` relative to
   `css/`, i.e. `css/fonts/…` — all 72 of which 404. The real files are at `fonts/lato/…` and all
   72 are present and served. This one is **not** in the staging repo README's list of gaps. It is
   cosmetic today (the browser silently falls back to a system sans-serif) but means the site is
   paying to host 23.4 MB of fonts that no page can actually load. Worth raising with John: fixing
   the path turns the fonts on, and deleting the unused weights would cut the site's size by about
   half. Either is a decision for him, not for this step.

A fourth, `chemaxon_logo.jpg`, returns `403 Forbidden` rather than 404 — present but unreadable.

---

## 4. Both sites, side by side

| | www.f3lcontestseries.org | www.mcneilco.com |
|---|---|---|
| Source of truth | This repo | Staging repo on Mika (`~/Projects/JMCo/mcneilco.com-site`) |
| Pages | 8 HTML | 7 HTML + 2 to be converted from PHP |
| Published files | 31 | 177 per the staging repo (131 verified by crawl) |
| Size | 33.4 MB | 71 MB per the staging repo (48.5 MB verified) |
| Dominated by | Photos (32 MB of 33) | Webfonts (23 MB) and PDFs (15 MB) |
| Downloads | One `.doc`, 56 KB, filename has spaces | Four PDFs, 15.2 MB |
| Server-side code | None | Three PHP files, already resolved in staging |
| Third-party embeds | Two F3XVault iframes on `results.html` | None |
| Links | All relative | All relative |
| Deploy today | `deploy/deploy.py` over FTP, dry run by default | None — hand FTP |

Combined, the two sites are about **105 MB and roughly 210 files** at the outside. Both are
effectively zero-traffic. Any host under consideration will treat this as a rounding error; price
will turn on **minimums and fixed monthly floors**, not on usage.

---

## 5. How they are hosted today

### 5.1 One shared account

Both sites are served from a single shared FatCow / iPage / Network Solutions account, $368.99/yr,
paid 2026-06-25, covered to about June 2027. F3L lives in `/f3l_series` **under the mcneilco.com
document root**.

### 5.2 The separation is not real today

Confirmed 2026-10-15:

| URL | Result |
|---|---|
| `http://www.mcneilco.com/f3l_series/` | **200** — serves the F3L home page (6,469 bytes, identical to `index.html`) |
| `http://www.mcneilco.com/f3l_series/index.html` | **200** — same |
| `http://www.f3lcontestseries.org/acas.html` | 404 |
| `http://www.f3lcontestseries.org/f3l_series/` | 404 |

So the entire F3L site is **publicly served under the mcneilco.com hostname as well as its own**.
The two sites are one filesystem with two names pointed at it, and a single FTP credential reaches
both. This is the concrete thing R5 (§8) has to end: not just separate billing, but no shared
document root, no shared credential, and no path on one site that serves the other.

### 5.3 There is no working HTTPS on either site today

Both hostnames answer on port 443 and complete a TLS handshake, but with the shared host's default
certificate:

- Subject `CN=*.bizland.com`, issuer `DigiCert / RapidSSL TLS RSA CA G1`, expires 2027-02-26.
- The chain is valid, but the name matches **neither** domain. `curl` without `-k` fails with
  `SSL: no alternative certificate subject name matches target host name`.

So `https://www.f3lcontestseries.org/` and `https://www.mcneilco.com/` both present a browser
name-mismatch warning. **Neither site has usable HTTPS.** R2 (§8) is new capability, not a
migration of something that already works — which also means there is no certificate to preserve
and nothing to break by moving.

Neither domain has a **CAA record**, so any CA may issue. ACM, Let's Encrypt and the hosts' built-in
issuers are all unblocked. Nothing needs changing for a certificate to be issued.

### 5.4 Redirects in use: effectively none

| Probe | Result |
|---|---|
| `http://f3lcontestseries.org/` | 200 direct, no redirect |
| `http://www.f3lcontestseries.org/` | 200 direct, no redirect |
| `http://mcneilco.com/` | 200 direct, no redirect |
| `http://www.mcneilco.com/` | 200 direct, no redirect |
| `http://www.mcneilco.com/stats/` | 302 → `https://www.bizland.com/controlpanel/stats/user_redir.html` |

**There is no bare-to-www redirect on either site, and no HTTP-to-HTTPS redirect.** Bare and www
both serve the same content at 200, from the same A record. The only redirect anywhere is `/stats/`,
which is the shared host's own control-panel plumbing and disappears with the host — it is not site
content and must not be reproduced.

So the bare-to-www behaviour John asks for in R3 is **new**, not something to preserve. Today both
names resolve to the same place and nothing canonicalises them.

Other observable server behaviour worth carrying over:

- Directory listings are **off** — `/assets/`, `/tutorials/`, `/fonts/` all return 403.
- A missing page returns a **404 with a real HTML body** (867 bytes, the host's generic page).
  Neither site ships a custom `404.html`; the new host's default is acceptable, but it should be a
  404 and not a 200 or a redirect to the home page.
- Paths are **case-sensitive** (`/Index.html` → 404). S3 and the CDN hosts behave the same way, so
  this is a non-issue, but a case-insensitive host would be a change in behaviour.
- `robots.txt` exists and is **empty** (0 bytes); there is no `sitemap.xml` (404).
- The live host rejects unrecognised user-agents with `HTTP 465`. The new host must **not** do this
  — it blocks scripted deploys and link checkers.

---

## 6. DNS facts

Verified by `dig` against 8.8.8.8 on 2026-10-15. All the card's facts confirmed; one correction.

### www.f3lcontestseries.org

| Record | Value | TTL |
|---|---|---|
| Registrar | Squarespace Domains, expires **2028-07-02** | — |
| Authoritative NS | `ns-cloud-d{1,2,3,4}.googledomains.com` (Google Cloud DNS) | — |
| `f3lcontestseries.org` A | `65.254.248.183` | 14400 (4 h) |
| `www` | **CNAME** → `f3lcontestseries.org` | 14400 (4 h) |

### www.mcneilco.com

| Record | Value | TTL |
|---|---|---|
| Registrar | Network Solutions, expires **2027-06-13** | — |
| Authoritative NS | `ns75.worldnic.com`, `ns76.worldnic.com` (Network Solutions) | — |
| `mcneilco.com` A | `65.254.248.220` | 7200 (2 h) |
| `www.mcneilco.com` | **A** → `65.254.248.220` | 7200 (2 h) |

> **Correction to the card.** The card describes the F3L www as a CNAME, which is right, but says
> nothing about mcneilco's. `www.mcneilco.com` is an **A record, not a CNAME** — the two sites are
> not symmetric. This matters: pointing a www A record at a CDN means either swapping it for a CNAME
> or tracking the provider's IPs by hand.

### What this means for the comparison

- **Bare-domain apex.** Both apexes are A records, and a CNAME at the apex is illegal. Any host
  reached by hostname rather than fixed IP needs either ALIAS/ANAME support at the apex or the
  provider's own DNS. **Google Cloud DNS has no ALIAS/ANAME record type.** So for F3L, "leave DNS in
  place" and "put the apex on a CDN hostname" cannot both hold — the comparison must say, per
  candidate, whether the apex works with the zone where it is. Network Solutions' DNS should be
  checked for ALIAS support the same way; assume it has none until shown otherwise.
- **An easy out.** Since the bare domain only has to **redirect** to www (R3), the apex does not
  need to reach the real origin — it needs to reach something that can issue a 301. That is a much
  weaker requirement and some candidates satisfy it cheaply. The comparison should treat
  "apex redirect" and "apex origin" as separate questions.
- **TTLs are long** — 4 h for F3L, 2 h for mcneilco. Both should be dropped to 300 s at least 24 h
  before any cutover, and raised again afterwards. That is a migration-plan item (task 3), noted
  here so it is not forgotten.
- Registrars stay where they are (R7). Only the records that point at hosting change.

---

## 7. Mail facts

**Neither domain's mail is on the web host.** Moving hosting does not move mail — provided the MX
and TXT records are left strictly alone.

| | f3lcontestseries.org | mcneilco.com |
|---|---|---|
| Provider | Mailgun | Google Workspace |
| MX | `10 mxa.mailgun.org`, `10 mxb.mailgun.org` | `1 aspmx.l.google.com`, `5 alt1`, `5 alt2`, `10 alt3`, `10 alt4 .aspmx.l.google.com` |
| SPF | `v=spf1 include:mailgun.org ~all` | **none at the apex** |
| DMARC | none | none |
| CAA | none | none |

Two things to carry forward:

- **`mcneilco.com` publishes no SPF record** despite running Google Workspace. Checked against both
  8.8.8.8 and 1.1.1.1 on 2026-10-15; the apex has no TXT records at all. This is a pre-existing mail
  hygiene gap, unrelated to hosting, and out of scope for this step — but it should not be mistaken
  for something the migration broke. Worth a separate card.
- The shared host also carries a `Maildir/` (per the card's description of the backup). Before the
  iPage account is cancelled, someone must confirm nothing is still delivering there. That is a
  migration-plan and cancellation item, not a hosting requirement.

**Hard constraint:** the DNS cutover touches A/AAAA/CNAME records for `@` and `www` only. MX and TXT
records are not to be edited, recreated, or migrated to a new DNS provider without separately
verifying them — and if a candidate requires moving the whole zone (e.g. Route 53), the comparison
must count copying MX and SPF across as part of its cost and risk.

---

## 8. Requirements

Numbered so the comparison and the migration plan can cite them. R1–R7 are John's, from the step
card (2026-10-14); R8–R12 are drawn from the inventory above.

| # | Requirement | Source |
|---|---|---|
| **R1** | **Static only, permanently.** Page vending and file downloads, nothing else. No forms, no uploads, no server-side code, ever. A host that offers PHP is not disqualified, but nothing may depend on it. | John |
| **R2** | **HTTPS with a certificate that renews itself.** No manual renewal, no calendar reminder. Note this is new capability — see §5.3. | John |
| **R3** | **The bare domain ends up on the www name.** `example.com` → `www.example.com`, ideally 301. New behaviour — see §5.4, and §6 on the apex problem. | John |
| **R4** | **Easy to manage, fair price at very little traffic.** Judge on minimums and fixed floors, not usage. An AWS account — John's existing personal one or a new one — serving from S3 is acceptable. **Never a client account.** | John |
| **R5** | **Two separate hosting setups, cleanly apart.** Not one shared account. Separate enough that a credential or mistake on one cannot reach the other. See §5.2 for how badly this fails today. | John |
| **R6** | **A scripted deploy with a dry run first**, runnable by John or a step worker, as `deploy/deploy.py` is today: show the plan, change nothing, then the same command with a flag to publish. | John |
| **R7** | **Domains stay where they are registered.** Squarespace Domains and Network Solutions keep the registrations. Only the DNS records pointing at hosting change. | John |
| **R8** | **Downloads must download.** The F3L `.doc` with **spaces in its filename**, and the four mcneilco PDFs up to 6.7 MB, must serve at their existing paths under their existing names, with a sane content type, and must not be forced inline or renamed. | §2.5, §3.4 |
| **R9** | **Existing paths keep working.** All links on both sites are relative and both sites move to a document root. No path rewriting is needed, and none should be introduced. Directory listings stay off; a missing path returns 404, not 200 and not a redirect to the home page. | §2.4, §5.4 |
| **R10** | **Mail is untouched.** MX and TXT records for both domains stay exactly as they are (§7). Any candidate requiring a zone move must account for carrying them across. | §7 |
| **R11** | **No user-agent filtering or bot interstitial.** The current host returns `HTTP 465` to unknown agents, which breaks scripted deploys and link checking. The new host must serve a plain client. | §5.4 |
| **R12** | **An exit that is a file copy.** Both sites are plain files with relative links. Whatever is chosen, leaving must mean copying a directory tree elsewhere and changing DNS — no proprietary build, no host-specific config that has to be reverse-engineered. | R4, §4 |

### Explicitly out of scope

Not requirements, and not to be solved by the choice of host: fixing the three broken references in
§3.5; the missing SPF record in §7; optimising the 32 MB of F3L photos or the 23 MB of unused Lato
fonts; adding a custom 404 page, a sitemap, or analytics. Several are worth doing — they are
separate cards, and §3.5 and §7 flag the ones John should see.

---

## 9. What the comparison has to answer

For each candidate, per site. This is the checklist task 2 should fill in.

1. **Monthly cost at near-zero traffic**, including any fixed minimum, the free-tier cliff, and what
   happens when a free tier ends. State the date the price was read.
2. **R2** — who issues the certificate, is renewal genuinely automatic, and what happens if it fails.
3. **R3** — how the apex is handled, given §6: is it an ALIAS/ANAME the current zone cannot provide,
   a redirect-only service, a fixed IP, or does it force a zone move?
4. **R6** — is a scripted deploy with a real dry run available, and is it a first-class CLI or a
   scraped web UI? For F3L, how much of `deploy/deploy.py` survives.
5. **DNS changes required**, record by record, and whether the zone has to move (and so whether R10
   turns into work).
6. **R5** — how two sites stay administratively apart: separate accounts, separate projects within
   one account, or separate credentials only. Say which, and what one site's compromised credential
   would reach.
7. **Admin effort over a year** — logins, renewals, billing changes, anything that expires.
8. **Lock-in and how to leave** (R12), including whether the files can be retrieved in bulk.
9. **The payload limits that actually bind here:** F3L's 6.5 MB single images and mcneilco's ~180
   files, against any per-file, per-deploy, per-site or per-month build limit.

A candidate that fails R1, R5, R7 or R10 should be ruled out rather than scored.

---

## 10. Open questions for John

None of these block task 2.

1. **The Lato fonts (§3.5, item 3).** Their stylesheet path is wrong, so no page has ever loaded
   them. Fix the path and turn them on, or delete them and halve the site? Either is fine; nobody
   should carry 23 MB of unreachable fonts to a new host without deciding on purpose.
2. **The missing `McNeilCoDataViewer.pdf` (§3.5, item 1).** Does a copy exist to restore, or should
   the link go?
3. **`mcneilco.com` has no SPF record (§7).** Out of scope here, but someone should open a card.
4. **The 177-file / 131-file gap (§1).** Confirm against the staging repo on Mika before the
   migration plan settles a payload size.
