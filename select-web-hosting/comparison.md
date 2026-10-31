# Host comparison — www.f3lcontestseries.org and www.mcneilco.com

Written 2026-10-15 for step "Select web hosting" (https://trello.com/c/DJy1ViGr), task W9dUxgGA.

Input to this document is `select-web-hosting/requirements.md` (same folder). Requirement numbers
**R1–R12** and section references (§) below are its numbering, not re-stated here.

**Nothing was bought, no account was created, no DNS record or site file was touched.** Every price
and limit below was read from the vendor's own page on **2026-10-15**; §8 lists every source with
the date read. Prices change — anything acted on after about January 2027 should be re-checked.

---

## 1. The answer first

| | Recommendation | Runner-up |
|---|---|---|
| **www.f3lcontestseries.org** | **AWS S3 + CloudFront + ACM, DNS left at Google Cloud DNS** — ~$0.01/mo | **GitHub Pages** — $0 if the repo goes public, $48/yr if it stays private |
| **www.mcneilco.com** | **AWS S3 + CloudFront + ACM, in a second AWS account, with the zone moved to Route 53** — $0.50/mo | **Netlify Free** — $0, and the only candidate needing no zone move for this domain |

Both sites on the recommended path: **about $6.25/year**, against **$368.99/year** today.

Two findings drive these picks, and both are corrections to assumptions carried into this step:

1. **Google Cloud DNS *does* support ALIAS records at the zone apex.** `requirements.md` §6 states it
   does not, and builds a whole "apex redirect vs apex origin" argument on that. Google's own record
   reference lists ALIAS as a Cloud DNS custom record type, apex-only, answering A/AAAA queries
   ([source A6](#8-sources)). It has two conditions, both of which f3lcontestseries.org already
   meets: the zone must be public (it is), and DNSSEC must be off (confirmed by `dig` — no DS and no
   DNSKEY at either apex, 2026-10-15). It must be created with `gcloud`/the API, not the console.
   **So for F3L, "leave DNS where it is" and "put the apex on a CDN" both hold.** That removes the
   single biggest objection to AWS for that site.
2. **Network Solutions DNS supports no ALIAS or ANAME, and no apex CNAME** ([source G2](#8-sources)).
   So mcneilco.com is the opposite case: its apex cannot reach any hostname-addressed host while its
   zone stays where it is. Every candidate for that site either moves the zone, or gives out a fixed
   IP for the apex.

That asymmetry is why the two sites get different runners-up. It is not inconsistency; the sites
differ in DNS provider, in commercial character, and in whether they are already a GitHub repo.

---

## 2. Ruled out rather than scored

`requirements.md` §9 says a candidate failing R1, R5, R7 or R10 is ruled out, not scored.

**GitHub Pages is ruled out for www.mcneilco.com — not on price or capability, on the product's own
prohibited-uses clause.** GitHub Pages' limits page says ([source C2](#8-sources)):

> "GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your
> online business, e-commerce site, or any other website that is primarily directed at either
> facilitating commercial transactions or providing commercial software as a service (SaaS)."

www.mcneilco.com is a product site for ACAS — seven pages of features, partner and sales pages, and
four product manuals. It is a commercial software vendor's brochure site. That is the thing the
clause names. This is a Pages *product* policy, not a plan limit, so paying for GitHub Pro does not
buy past it. Hosting a site there against the clause means its availability depends on nobody at
GitHub reading it the same way; that is not a foundation for a business site John is trying to stop
worrying about. **Ruled out.**

The clause does not catch www.f3lcontestseries.org. It is a volunteer contest series' schedule,
results and rules — no transactions, no SaaS, nothing sold.

**Nothing else is ruled out.** No candidate fails R1 (all are static-file hosts; none requires
server code). No candidate fails R7 (every one keeps the registration where it is — a nameserver
change is not a registrar change). R10 is satisfied by every candidate *provided* the MX and TXT
records are carried correctly where a zone moves; §5 counts that work per candidate rather than
disqualifying anyone for it.

---

## 3. Cost at near-zero traffic

Computed from the payloads measured in `requirements.md`: **F3L 33.4 MB / 31 files**, **mcneilco.com
71 MB / 177 files** (§4 there). Traffic assumed at effectively zero — under 1 GB/month and under
10,000 requests/month for either site. All prices read 2026-10-15.

| Candidate | F3L / month | mcneilco / month | What the money actually is |
|---|---:|---:|---|
| AWS S3 + CloudFront + ACM, DNS in place | **~$0.01** | **~$0.01** | S3 storage only; CloudFront and ACM are $0 at this volume |
| AWS + Route 53 for the zone | **$0.50** | **$0.50** | the above plus one hosted zone |
| GitHub Pages, public repo | **$0** | — *(ruled out)* | nothing |
| GitHub Pages, private repo | **$4.00** | — *(ruled out)* | GitHub Pro, $48/yr |
| Cloudflare Pages Free | **$0** | **$0** | nothing |
| Netlify Free | **$0** | **$0** | nothing, but a 300-credit/month hard cap |
| NearlyFreeSpeech, Non-Production realm | **$0.34** | **$0.37** | $0.01/day base + $1.00/GiB-month storage |
| NearlyFreeSpeech, Production realm | **$1.55** | **$1.59** | $0.05/day base + storage |
| Bunny.net (own account per site) | **$1.00** | **$1.00** | entirely the $1 account minimum |

### How each number was derived

**AWS, DNS in place.** S3 Standard is $0.023/GB-month in US East/US West with no minimum and no
minimum storage duration ([A1](#8-sources)). F3L: 0.0326 GiB × $0.023 = **$0.00075/month**.
mcneilco: 0.0693 GiB × $0.023 = **$0.00159/month**. Deploy PUTs are $0.005/1,000 — 31 objects is
$0.00016, 177 objects is $0.00089, and incremental deploys are a fraction of that. **S3 → CloudFront
data transfer is free** ([A1](#8-sources)), so visitor traffic generates no S3 egress at all.
CloudFront pay-as-you-go has an **always-free tier of 1 TB egress and 10,000,000 HTTP/HTTPS requests
per month** ([A2](#8-sources)) — three to four orders of magnitude above either site's traffic.
Invalidations: the first 1,000 paths per month are free ([A2](#8-sources)), and a deploy needs one
(`/*` counts as one path). An ACM public certificate for an integrated service is **$0**
([A4](#8-sources)). The bill is therefore the storage line and nothing else: **under $0.05 per site
per year.** It will show on the invoice as $0.01/month because of rounding.

**AWS + Route 53.** Add **$0.50 per hosted zone per month** for the first 25 zones
([A5](#8-sources)) — $6.00/year. Query charges are $0.40/million, and **alias A/AAAA records
pointing at a CloudFront distribution incur no query charge at all** ([A5](#8-sources)); residual
non-alias queries at this traffic are a fraction of a cent. Hosted zones are **not** in the free
tier. Monthly zone fees are not prorated.

**GitHub Pages.** $0 from a public repository. The F3L repo is private, and Pages from a private
repository on a personal account requires **GitHub Pro, $4/month** ([C3](#8-sources), [C4](#8-sources)) —
$48/year, which is 1,000× the AWS bill for the same site. Two honest ways out: make the repo public
(it is a club website; there is nothing in it that isn't already on the public internet), or accept
$48/yr. Note that Pro is one subscription covering all of John's private repos, so the *marginal*
cost of a second private-repo Pages site is $0 — but putting both sites under one GitHub account is
exactly the shared-blast-radius arrangement R5 exists to end, and mcneilco.com is ruled out anyway.

**Cloudflare Pages.** Free plan, $0: 500 builds/month, 1 concurrent build, 20,000 files per
deployment, 25 MiB maximum per file, 100 custom domains per project ([D1](#8-sources)). Bandwidth
and requests are not metered on Pages. Nothing here binds: F3L's largest single file is
`assets/wagon.jpg` at 6.55 MB, and 177 files is under 1% of the file cap. Cloudflare DNS for the
zone is also free. **This is the cheapest candidate with no minimum and no cap** — its costs are in
§4–§6, not here.

**Netlify Free.** $0, and the plan is **300 credits per month** ([E1](#8-sources)). Netlify's own
pricing page prices the credits: a **production deploy is 15 credits**, **bandwidth is 20 credits
per GB**, and **web requests are 2 credits per 10,000** ([E1](#8-sources)). So 300 credits is
**20 production deploys a month with zero traffic**, or 15 GB of transfer with zero deploys, or any
mix. At the real usage here — a handful of deploys a year and well under 1 GB/month — the cap is not
close. Two cautions. First, it is a **hard cap with no overage on the Free plan**: credits do not
roll over, automatic recharge is unavailable, and when the balance is exhausted Netlify stops
credit-consuming activity rather than billing. Second, Netlify has **already re-priced the credits
once**, doubling bandwidth from 10 to 20 credits/GB and compute from 5 to 10, while leaving the Free
allowance at 300 — i.e. each credit bought half as much after the change. The next paid step is
Personal at **$9/month** for 1,000 credits. Treat Netlify Free as free-for-now with a floor that can
be moved under you, and a failure mode that is *the site pausing*, not a surprise invoice.

**NearlyFreeSpeech.NET.** Pay-as-you-go with **no monthly minimum**; an account opens on a deposit
of as little as $0.25 ([F1](#8-sources)). Per-site base charge is **$0.01/day** in the
Non-Production realm (1 GiB/day bandwidth included) and **$0.05/day** in Production (10 GiB/day);
storage is **$1.00/GiB-month** in every realm, and extra bandwidth is currently billed at **$0.00/GiB**
([F2](#8-sources)). F3L at 0.0326 GiB: $0.304 base + $0.033 storage = **$0.34/month ($4.07/yr)**
non-production, **$1.55/month ($18.65/yr)** production. mcneilco at 0.0693 GiB: **$0.37/month
($4.49/yr)** non-production, **$1.59/month ($19.08/yr)** production. The realm choice is not free:
Non-Production is described as intended for personal sites, beta sites and experiments, and
**"Non-Production Sites must constitute no more than half of the sites on your membership, rounded
up"** ([F2](#8-sources)) — one site alone on a membership can be non-production. A live public
commercial site belongs in Production; a club site is arguable. The honest planning numbers are
therefore about **$4/yr for F3L** and about **$19/yr for mcneilco.com**.

Note the storage price is the one place where these payloads are not a rounding error. At
$1.00/GiB-month, mcneilco.com's **23.4 MB of Lato webfonts that no page can load**
(`requirements.md` §3.5 item 3) cost about **$0.27/year** on their own — trivial, but it is the only
candidate where deleting them shows up on the bill at all.

**Bunny.net.** Storage is $0.01/GB-month for a single standard (HDD) region, CDN delivery is
$0.01/GB in North America and Europe, and there are **no request or API fees**
([H1](#8-sources), [H2](#8-sources)). For these sites that is **$0.0003–0.0007/month of storage and
pennies of transfer** — so the bill is entirely the **$1.00 monthly account minimum**
([H1](#8-sources)). Bunny DNS is free for up to 500 zones ([H3](#8-sources)). One account with two
storage zones costs $12/yr but shares a credential across both sites; two accounts, which is what
R5 wants, cost **$24/yr**. There is no free tier, only a 14-day trial.

### The thing to notice about this table

At this traffic every candidate is between $0 and $24 a year. **Price is not the deciding factor
and should not be treated as one** — the spread across the whole table is less than 7% of what the
shared iPage account costs today. The decision turns on §4 (certificates), §5 (the apex and the DNS
work), §6 (the deploy script), §7 (separation, admin and lock-in). Price only matters where it is
*structural*: a hard cap that can pause the site (Netlify), a floor the vendor can move (Netlify
credits), or a subscription that exists only to unlock the feature (GitHub Pro).

### Two cost traps that are not in the table

- **A new AWS account is now enrolled in a "Free account plan" that expires.** AWS changed the free
  tier in 2025: a new account gets up to $200 in credits and access to a restricted subset of
  services, for **6 months or until the credits run out**, and then **"AWS suspends your account and
  any associated projects, and you will lose access to your resources and data"**, with data
  retained 90 days before permanent erasure ([A3](#8-sources)). Always-free service tiers (such as
  CloudFront's 1 TB) continue on a paid account. **Any new AWS account created for this must be
  switched to the Paid account plan immediately** — before anything is hosted on it, not after. An
  existing personal AWS account is not affected, and is the lower-risk starting point. This belongs
  in the migration plan as a step with a checkbox.
- **Cloudflare Pages' Direct Upload is a one-way door.** Cloudflare's own documentation: *"if you
  choose Direct Upload, you cannot switch to Git integration later"* ([D2](#8-sources)). Not a cost,
  but an irreversible setup choice that has to be made before the first deploy.

---

## 4. R2 — HTTPS with a certificate that renews itself

Every candidate satisfies R2. They differ in who you depend on and what failure looks like.
Remember from `requirements.md` §5.3 that **neither site has working HTTPS today** — both serve a
valid-chain `CN=*.bizland.com` certificate matching neither domain — so this is new capability and
there is no existing certificate to preserve. Neither domain has a CAA record, so no issuer is
blocked.

| Candidate | Issuer | Renewal | If it fails |
|---|---|---|---|
| AWS (ACM) | Amazon Trust Services, via ACM | Automatic, free, managed by AWS for the life of the distribution | ACM emails and retries; DNS-validated certs renew silently as long as the validation CNAME stays in the zone |
| GitHub Pages | Let's Encrypt | Automatic, managed by GitHub | Breaks if DNS records drift — extra A/AAAA/ALIAS/CNAME records block issuance; fix is remove and re-add the domain |
| Cloudflare Pages | Cloudflare (Universal SSL) | Automatic | Zone must be on Cloudflare; CAA records can block issuance |
| Netlify | Let's Encrypt | *"Certificates are generated and renewed automatically as needed"*, free on all plans including Free | Requires DNS already pointing at Netlify, and aliases configured in advance to be on the certificate |
| NearlyFreeSpeech | Let's Encrypt | Automatic since 2024-05 for all sites — *"you don't have to do anything to set it up, and you don't have to do anything to renew it"* | Needs the alias resolving to the site; retries |
| Bunny.net | Let's Encrypt | *"free auto-renewing SSL certificates"*, enabled per hostname with one click | Needs the hostname CNAME'd to the pull zone first |

Sources: [A4](#8-sources), [C5](#8-sources), [D3](#8-sources), [E3](#8-sources), [F3](#8-sources),
[H4](#8-sources).

Two practical notes:

- **ACM for CloudFront must be issued in us-east-1**, whatever region the bucket is in. It is a
  standing trip-hazard in every AWS static-site walkthrough and belongs in the migration plan.
- **One certificate must cover both the apex and the www name** on every candidate, because R3 means
  `https://f3lcontestseries.org/` has to terminate TLS before it can 301. A redirect served over
  plain HTTP only is a partial pass on R3 — see §5.

**All six are genuinely hands-off.** R2 does not separate the candidates.

---

## 5. R3 and the DNS work — where the candidates really differ

This is the section that decides it. `requirements.md` §6 is right that both apexes are A records
and a CNAME at an apex is illegal; it is wrong that Cloud DNS cannot do better (§1 above).

### The apex, per candidate, per site

| Candidate | f3lcontestseries.org apex (Google Cloud DNS) | mcneilco.com apex (Network Solutions) |
|---|---|---|
| AWS S3+CloudFront | **ALIAS → the distribution.** Works, zone stays. gcloud/API only, DNSSEC must stay off (both fine) | **Impossible as-is** — no ALIAS/ANAME, no apex CNAME. Needs the zone moved (Route 53, $6/yr) |
| GitHub Pages | **4 A records** to 185.199.108–111.153 (or 4 AAAA). Works on any provider, zone stays | *(ruled out — §2)* |
| Cloudflare Pages | **Zone must move to Cloudflare.** *"To deploy your Pages project to a custom apex domain, that custom domain must be a zone on the Cloudflare account"* | **Zone must move to Cloudflare** |
| Netlify | **1 A record** to 75.2.60.5 (or ALIAS → apex-loadbalancer.netlify.com). Works, zone stays | **1 A record** to 75.2.60.5. Works, **zone stays** |
| NearlyFreeSpeech | A records to the IPs in the site panel. Works, zone stays | Works, zone stays |
| Bunny.net | **Zone must move to Bunny DNS** (free) — a PullZone or CNAME record at the apex is auto-flattened to A/AAAA | **Zone must move to Bunny DNS** |

Sources: [A6](#8-sources), [C1](#8-sources), [D4](#8-sources), [E2](#8-sources), [F4](#8-sources),
[H5](#8-sources).

### Bare → www, per candidate

| Candidate | How the 301 happens | Over HTTPS? |
|---|---|---|
| GitHub Pages | **Free and automatic.** Set `www.example.com` as the custom domain and have both apex and www records in place; *"`example.com` will redirect to `www.example.com`"* | Yes, Pages certificates cover both names |
| Netlify | Automatic. Netlify adds both apex and www to the site when either is assigned, and redirects the non-primary to the primary | Yes |
| NearlyFreeSpeech | Add both names as aliases, set **canonical name redirection** on; non-canonical aliases get a **301 Moved Permanently** to the canonical name | Yes — automatic TLS covers aliases |
| Cloudflare Pages | A **Single Redirect** rule; the Free plan allows 10 rules with wildcard support | Yes |
| Bunny.net | Native **Redirect (RDR)** record in Bunny DNS, or a second pull zone | Yes |
| AWS S3+CloudFront | Needs building. Either (a) a **CloudFront Function** on viewer-request that 301s when `Host` is the apex — one distribution, one certificate, 2M free invocations/month; or (b) a **second distribution** fronting an S3 bucket set to *"Redirect requests for an object"* with host `www.…` and protocol `https`, which S3's website endpoint serves as a **301** | Yes, either way; the certificate must list both names |

Sources: [A2](#8-sources), [A7](#8-sources), [C1](#8-sources), [D5](#8-sources), [E2](#8-sources),
[F5](#8-sources), [H5](#8-sources).

`requirements.md` §6 suggested treating "apex redirect" and "apex origin" as separate questions, on
the assumption the apex could not reach a CDN at all. With ALIAS available on Cloud DNS the
distinction stops mattering for F3L — and for mcneilco.com, the apex has to reach *something* with a
certificate for its own name either way, so a redirect-only apex is no cheaper than an origin apex.
**One route worth naming and rejecting:** Network Solutions offers "web forwarding" as its
substitute for ALIAS. It would redirect `mcneilco.com` without touching the zone, but it is an HTTP
forwarder with no certificate for the bare name, so `https://mcneilco.com/` would still fail. That
is no worse than today, and it is still a partial pass on R3. Don't plan on it.

### Record-by-record DNS changes, for the recommended and runner-up paths

**F3L on AWS, zone stays at Google Cloud DNS — 3 changes, 1 of them temporary:**

| Record | Today | After |
|---|---|---|
| `f3lcontestseries.org` | A 65.254.248.183, TTL 14400 | **ALIAS** → `dXXXX.cloudfront.net` |
| `www.f3lcontestseries.org` | CNAME → `f3lcontestseries.org`, TTL 14400 | **CNAME** → `dXXXX.cloudfront.net` |
| `_xxxx.f3lcontestseries.org` | — | **CNAME** (ACM DNS validation) — add before cutover, then leave in place so renewal keeps working |
| MX, SPF TXT | Mailgun | **untouched** |

**mcneilco.com on AWS, zone moves to Route 53 — the whole zone is recreated:**

| Record | Today | After |
|---|---|---|
| `mcneilco.com` | A 65.254.248.220, TTL 7200 | **Alias A** → the CloudFront distribution |
| `www.mcneilco.com` | **A** 65.254.248.220, TTL 7200 | **Alias A** or CNAME → the distribution *(note: today this is an A record, not a CNAME — the two sites are not symmetric)* |
| MX ×5 | `aspmx.l.google.com` + alt1–alt4 | **copied verbatim, verified before the NS change** |
| TXT | *none at the apex* | nothing to copy — and nothing to add; the missing SPF record is out of scope (`requirements.md` §7) |
| `_xxxx.mcneilco.com` | — | ACM validation CNAME |
| NS at the registrar | `ns75/ns76.worldnic.com` | the four Route 53 nameservers |

**mcneilco.com on Netlify, zone stays at Network Solutions — 2 changes:**

| Record | Today | After |
|---|---|---|
| `mcneilco.com` | A 65.254.248.220 | **A → 75.2.60.5** |
| `www.mcneilco.com` | A 65.254.248.220 | **CNAME → `<project>.netlify.app`** |
| MX ×5, everything else | Google Workspace | **untouched** |

**That contrast is the whole argument for Netlify as mcneilco.com's runner-up.** The AWS path for
that site requires moving a zone that carries live Google Workspace mail; the Netlify path changes
two records and never goes near the MX. A zone move is not hard, but it is the one step in this
whole migration where a mistake takes down John's email rather than a website — and R10 is explicit
that the cost of carrying MX across counts against the candidate that requires it.

**TTLs.** Both zones are long — 14400 s for F3L, 7200 s for mcneilco. Drop the records being changed
to 300 s at least 24 hours before cutover (longer than the old TTL, so every resolver has seen the
short value), cut over, then raise them again. This is a migration-plan item; recorded here so task
3 does not have to rediscover it.

---

## 6. R6 — scripted deploy with a dry run

`deploy/deploy.py` today: dry run is the **default**, it connects, compares the local deploy set
against a manifest it keeps on the server, prints the plan, sends nothing; `--upload` performs it,
with `--delete`, `--force`, `--allow-dirty` and `--verbose` alongside. That is the bar. The useful
question is not "can it be scripted" — all six can — but **is the dry run a real connect-and-compare
against what is live, or a local guess?**

| Candidate | Deploy | Dry run | Honest grade |
|---|---|---|---|
| **AWS** | `aws s3 sync ./site s3://bucket --delete` then one `aws cloudfront create-invalidation` | **`aws s3 sync --dryrun`** — *"displays the operations that would be performed … without actually running them"*, against the real bucket listing, honouring `--delete` and `--exclude` | **Best fit.** A first-class vendor CLI doing exactly what deploy.py hand-rolls. The manifest file, the `.uploading` rename dance and the FTP error handling — most of deploy.py — all get **deleted**, not ported |
| **GitHub Pages** | `git push`; Pages builds and publishes | No connect-and-compare. But `git status` / `git diff` *is* the plan, reviewable before the push, and `deploy/preview.sh` already serves the tree locally | **Different, arguably better.** The plan is a reviewable diff in version control rather than a printout. It is not what R6 literally describes |
| **Netlify** | `netlify deploy` → draft URL; `netlify deploy --prod` | Better than a dry run: a **real staged deploy at its own URL** that you can click through before promoting | **Strong**, with a caveat — each production deploy costs 15 of the month's 300 credits |
| **Cloudflare Pages** | `npx wrangler pages deploy ./site` | **No dry-run flag.** Substitute is `--branch=<name>` for a preview deployment at its own URL | **Weakest.** Also needs Node/npx, where everything else here is Python or a single static binary |
| **NearlyFreeSpeech** | `rsync` over SSH | **`rsync -n --delete`** — the original dry run, exact and local-to-remote | **Excellent, and closest in spirit to today.** A plain Unix host with real SSH |
| **Bunny.net** | Storage HTTP API (per-file PUT/DELETE), or FTP | Must be written. No vendor dry run either way | **Needs the most new code.** And its FTP has **"Encryption: Not supported"** — plaintext credentials; the docs call FTP *"outdated"* and point at the HTTP API instead |

Sources: [A8](#8-sources), [D2](#8-sources), [H6](#8-sources), and `deploy/deploy.py` read
2026-10-15.

Two payload-shaped notes (`requirements.md` §9 item 9):

- **Nothing binds.** F3L's largest file is 6.55 MB, well under Cloudflare Pages' 25 MiB per-file cap,
  the only per-file cap in the table. 177 files is under 1% of the 20,000-file deployment cap. No
  candidate has a per-deploy or per-month size limit that either site approaches.
- **R8, downloads.** The F3L bulletin template has **spaces in its filename**. Every candidate serves
  it (keys and paths with spaces are URL-encoded in transit), but on AWS the content type is set at
  upload time, not by the server: `aws s3 sync` guesses from the extension, and `.doc` must land as
  `application/msword` rather than `binary/octet-stream`. Pin it with `--content-type` or verify it
  after the first deploy. On the other candidates the server infers it per-request from the
  extension, and `_headers` (Cloudflare/Netlify) can override.
- **R9, a missing path must 404.** One real AWS gotcha: with a REST origin and Origin Access Control
  — the modern, correct way to front a private bucket with CloudFront — **a missing key returns 403
  AccessDenied, not 404**. A CloudFront custom error response mapping 403 → 404 is required to meet
  R9. Every other candidate returns a 404 by default. Put it in the migration plan's verification
  list.

---

## 7. R5 separation, admin effort, and lock-in

### R5 — how the two sites stay apart

`requirements.md` §5.2 measured how badly this fails today: the entire F3L site is publicly served
at `www.mcneilco.com/f3l_series/`, one document root with two names on it, one FTP credential
reaching both. R5 wants that ended three ways: separate billing, no shared document root, and no
credential that spans both.

| Candidate | Strongest available separation | What a compromised credential for one site reaches |
|---|---|---|
| **AWS, two accounts** | **Two separate AWS accounts.** Hard boundary — separate root identities, separate IAM, separate bills, no cross-account access unless explicitly granted | **That site's bucket only.** The best answer in the table |
| AWS, one account two buckets | Separate IAM users with bucket-scoped policies | That bucket, if the policy is right — but a root or over-broad credential reaches both, and one billing account |
| GitHub Pages | Separate repos; separate accounts if you want a real boundary | A repo-scoped token reaches one repo; an account-level PAT reaches every repo on the account |
| Cloudflare Pages | Separate Cloudflare accounts (two projects in one account share an API token scope) | One project, with a project-scoped token; the whole account with an account token |
| Netlify | Separate teams, or separate accounts | One site with a site-scoped token |
| NearlyFreeSpeech | **Separate memberships** — each has its own balance, its own SSH users, its own sites | That membership's sites only. Also very clean |
| Bunny.net | Separate accounts (storage-zone passwords are per-zone within an account) | One storage zone with a zone password; the whole account with an API key |

**Every candidate can satisfy R5 if you are willing to run two of whatever the vendor's account unit
is.** The recommendation puts mcneilco.com in a **second AWS account**, which is both the cleanest
boundary available anywhere in this comparison and the thing that most directly answers what is
wrong today. It also keeps R4's "never a client account" trivially true — mcneilco.com is John's own
company, not a client, and it gets its own account regardless.

### Admin effort over a year

Assume both sites change a handful of times a year — F3L has a schedule and results that move during
the season, mcneilco.com essentially never.

| Candidate | What recurs | Realistic hours/year |
|---|---|---|
| AWS | Nothing expires. One card on file, one invoice a month of about $0.01–$0.51. No renewals, no builds to babysit | **~0.5 h** — reading invoices |
| GitHub Pages | Nothing expires. GitHub Pro renews if the repo stays private | **~0.5 h** |
| Cloudflare Pages | Nothing expires. Cloudflare is now also the DNS provider, so DNS edits move there | **~0.5 h** |
| Netlify | **Credit budget is the recurring thing.** Not time-consuming, but it is a number that can be re-priced and a cap that pauses the site, so it wants an occasional glance | **~1 h** |
| NearlyFreeSpeech | **Prepaid balance must not run dry.** It is pay-as-you-go from a deposit — $4–19/yr means topping up rarely, but a forgotten balance stops the site. Two memberships means two balances | **~1–2 h** |
| Bunny.net | Prepaid balance, $1/month minimum draw per account | **~1 h** |

The difference between the best and worst here is an hour a year. Admin effort does not decide this
either — except to note that **the two prepaid candidates (NFSN, Bunny) add a recurring obligation
with a site-down failure mode**, and the card-on-file candidates do not.

### R12 — lock-in and how to leave

R12 asks that leaving be a file copy. Every candidate passes; the exits differ in effort.

| Candidate | Getting the files back | Host-specific config left behind |
|---|---|---|
| AWS | `aws s3 sync s3://bucket ./local` — one command, exact | Distribution + cert + bucket policy; all rebuildable, none of it in the content |
| GitHub Pages | `git clone` — you already have every byte | A `CNAME` file and a repo setting |
| Cloudflare Pages | **Weakest.** No "download my site" — the deployed artifact is not offered back. In practice you keep the source locally and re-upload elsewhere; `_headers`/`_redirects` are plain files | `_headers`, `_redirects`; and **Direct Upload cannot later become a Git integration** |
| Netlify | Deploys are downloadable from the UI; the source stays yours | `netlify.toml`, `_redirects` |
| NearlyFreeSpeech | `rsync` or `scp` the tree off | Essentially none — it is a Unix filesystem |
| Bunny.net | Storage API or FTP pull | Pull-zone settings |

**Both sites are plain files with relative links** (`requirements.md` §2.4, §4), which is what makes
R12 easy everywhere. The real lock-in risk in this comparison is not file retrieval — it is building
a deploy pipeline around a vendor-specific CLI. On that measure AWS, NFSN and GitHub are the most
portable (an S3 sync, an rsync, and a git push all have equivalents everywhere) and Cloudflare Pages
the least (`wrangler` is Cloudflare-only, and Direct Upload forecloses the Git path).

---

## 8. Sources

Every page read **2026-10-15** from Bishop. Prices and limits were read from the vendor's own
documentation or pricing page except where marked *(secondary)*; the three secondary items are
cross-checked against a primary source in the same row or are facts the vendor states only in a blog
post.

### AWS

- **A1** S3 pricing — https://aws.amazon.com/s3/pricing/ — S3 Standard $0.023/GB-month first 50 TB
  (US East/US West), PUT/COPY/POST/LIST $0.005/1,000, GET $0.0004/1,000, **no monthly minimum and no
  minimum storage duration for S3 Standard**, **data transfer to CloudFront free**.
- **A2** CloudFront pay-as-you-go pricing — https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/
  — always-free **1 TB egress + 10,000,000 HTTP/HTTPS requests + 2,000,000 CloudFront Function
  invocations per month**; $0.085/GB North America beyond; $0.0100/10,000 HTTPS requests; **custom
  SSL via SNI free**, dedicated IP $600/month; **first 1,000 invalidation paths/month free**, then
  $0.005/path; CloudFront Functions $0.10/million. Also read
  https://aws.amazon.com/cloudfront/pricing/ for the newer flat-rate plans (Free $0 / 1M requests /
  100 GB; Pro $15; Business $200; Premium $1,000) — pay-as-you-go and flat-rate coexist and are
  chosen per distribution. At this traffic both are $0.
- **A3** AWS Free Tier FAQs — https://aws.amazon.com/free/free-tier-faqs/ — the 2025 Free vs Paid
  **account plans**: new accounts get up to $200 credits, free plan lasts **6 months or until credits
  are exhausted**, then **"AWS suspends your account and any associated projects, and you will lose
  access to your resources and data"** with 90 days' data retention; always-free service tiers
  continue on a paid plan; existing/former account holders are ineligible for the free plan.
- **A4** ACM pricing — https://aws.amazon.com/certificate-manager/pricing/ — *"ACM issues
  certificates at no cost for use with services integrated with ACM."* ACME certificates $1.00/domain
  and exportable certificates $7.00 are separate products, not needed here.
- **A5** Route 53 pricing — https://aws.amazon.com/route53/pricing/ — **$0.50/hosted zone/month**
  first 25 zones, not in the free tier, not prorated (free if deleted within 12 hours of creation);
  standard queries $0.40/million first billion; **alias A/AAAA records to CloudFront distributions
  incur no charge**.
- **A6** Cloud DNS record types — https://docs.cloud.google.com/dns/docs/records-overview — supported
  types include **ALIAS**, a Cloud DNS custom record type that *"behaves like a CNAME record but can
  only be used at the zone apex and only responds to address record (A or AAAA) queries"*;
  **public zones only, not compatible with DNSSEC, and must be configured via the gcloud CLI or the
  Cloud DNS API rather than the console.** *(This is the finding that overturns `requirements.md` §6.)*
- **A7** S3 webpage redirects — https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html
  — *"Redirect requests for an object"* on a static-website-hosting bucket redirects **all** requests
  to a given host name, with **Protocol** selectable as `https`; served as a **301** from the
  **website endpoint** (the REST endpoint does not redirect).
- **A8** `aws s3 sync` reference — https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html —
  **`--dryrun`** *"displays the operations that would be performed using the specified command
  without actually running them"*; `--delete`, `--exclude`, `--size-only`, `--exact-timestamps`.

### GitHub Pages

- **C1** Managing a custom domain —
  https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
  — apex via **A records to 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153** (or
  the four AAAA, or ALIAS/ANAME); www via **CNAME to `<user>.github.io`**; and *"If you configure
  `www.example.com` as the custom domain for your site, and you have GitHub Pages DNS records set up
  for the apex and `www` domains, then `example.com` will redirect to `www.example.com`."*
- **C2** GitHub Pages limits —
  https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits — **1 GB
  published site**, 1 GB source repo recommended, **100 GB/month soft bandwidth limit**, **10
  builds/hour soft limit** (custom Actions workflows exempt), and the prohibited-uses clause quoted
  in §2 above.
- **C3** GitHub plans — https://docs.github.com/en/get-started/learning-about-github/githubs-plans
  and https://github.com/pricing — Pages in public repositories on all plans; **publishing a Pages
  site *privately* requires an organization on GitHub Enterprise Cloud**; and see
  https://docs.github.com/en/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site
  — *"To publish a GitHub Pages site privately, your organization must use GitHub Enterprise Cloud."*
  **Repository visibility and site visibility are separate**: a private repo can publish a fully
  public site.
- **C4** *(secondary)* GitHub Pro at **$4/user/month** — GitHub's pricing page did not render a Pro
  line when read on 2026-10-15 (it showed Free $0 and Team $4/user/month); $4/month for Pro is from
  secondary sources and **should be confirmed on github.com/pricing before John pays for it**. The
  requirement it unlocks — Pages from a private personal repo — is primary, from C3.
- **C5** Securing Pages with HTTPS —
  https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https
  — certificates come from **Let's Encrypt**, provisioned automatically once DNS is correct; **extra
  A/AAAA/ALIAS/ANAME/CNAME records can prevent issuance**; "Enforce HTTPS" is a setting that becomes
  available after provisioning.

### Cloudflare Pages

- **D1** Pages limits — https://developers.cloudflare.com/pages/platform/limits/ — Free: **500
  builds/month, 1 concurrent build, 20,000 files per deployment, 25 MiB maximum file size, 100
  custom domains per project, 100 projects per account**; bandwidth and requests not metered.
- **D2** Direct Upload — https://developers.cloudflare.com/pages/get-started/direct-upload/ —
  `npx wrangler pages deploy <dir>`, `--branch=<name>` for previews, **no dry-run option**, no Git
  connection required, and *"if you choose Direct Upload, you cannot switch to Git integration
  later."*
- **D3** Universal SSL is automatic for zones on Cloudflare — certificate provisioning and renewal
  are Cloudflare-managed; the Pages custom-domain documentation (D4) notes only that **CAA records
  can block issuance**.
- **D4** Pages custom domains — https://developers.cloudflare.com/pages/configuration/custom-domains/
  — subdomains via CNAME to `<project>.pages.dev` **after** adding the domain in the dashboard
  (otherwise a 522); and *"To deploy your Pages project to a custom apex domain, that custom domain
  must be a zone on the Cloudflare account"* — i.e. **nameservers must point at Cloudflare**.
- **D5** URL forwarding — https://developers.cloudflare.com/rules/url-forwarding/ — Free plan:
  **10 Single Redirect rules** with wildcard support (no regex), or Bulk Redirects with 15 rules /
  5 lists / 10,000 URLs; records must be proxied through Cloudflare.
- **D6** *(secondary)* Cloudflare's §2.8 "Limitation on Serving Non-HTML Content" was moved in the
  2023 terms refresh into CDN-specific terms, with content hosted on a Cloudflare service (Pages,
  R2, Images, Stream) expressly allowed. This matters because F3L is **99.6% photography**. The
  effect appears to be that Pages-hosted images are fine, but this was read from secondary coverage
  of the terms change, not the terms themselves — **confirm against
  https://www.cloudflare.com/terms/ before choosing Cloudflare Pages for F3L.**

### Netlify

- **E1** Pricing — https://www.netlify.com/pricing/ — Free **$0 with a 300-credit limit**, Personal
  **$9/month / 1,000 credits**, Pro **$20/month / 3,000 credits**; **production deploys 15 credits
  each, bandwidth 20 credits/GB, web requests 2 credits/10k**. *(secondary, cross-checked)* the
  credit model applies to accounts created after 2025-09-04 — legacy accounts keep 100 GB/300 build
  minutes; credits do not roll over, automatic recharge is unavailable on Free, and Netlify stops
  credit-consuming activity rather than billing overage; the per-credit rates for bandwidth and
  compute were doubled in a later revision while the Free allowance stayed at 300.
- **E2** External DNS — https://docs.netlify.com/manage/domains/configure-domains/configure-external-dns/
  — apex: **ALIAS/ANAME/flattened CNAME to `apex-loadbalancer.netlify.com`** where supported, else
  **A record to 75.2.60.5**; www: **CNAME to `<project>.netlify.app`**; *"If you assign an apex
  domain or a `www` subdomain to your site, Netlify will automatically add both the apex domain and
  the `www` subdomain."* DNS propagation up to 24 h.
- **E3** HTTPS/SSL — https://docs.netlify.com/manage/domains/secure-domains-with-https/https-ssl/ —
  **Let's Encrypt**; *"Netlify offers free HTTPS on all sites, including automatic certificate
  creation and renewal"*; *"Certificates are generated and renewed automatically as needed"*; DNS
  must already point at Netlify, and **aliases must be configured in advance to be included on the
  certificate**.

### NearlyFreeSpeech.NET

- **F1** Pricing overview — https://www.nearlyfreespeech.net/services/pricing — site base charges
  **$0.01/day non-production, $0.05/day production, $0.50/day critical**; account opens on a deposit
  of **as little as $0.25**; DNS hosting $0.01 per 9 days when the domain is both registered and
  hosted there.
- **F2** Hosting detail — https://www.nearlyfreespeech.net/services/hosting — included bandwidth
  **1 GiB/day non-production, 10 GiB/day production, 100 GiB/day critical**; storage **$1.00/GiB-month**
  in all realms; **extra bandwidth currently $0.00/GiB**; resources $0.01/44.64 RAUs; and
  *"Non-Production Sites must constitute no more than half of the sites on your membership, rounded
  up."*
- **F3** *(secondary)* Automatic TLS — NFSN's own blog, "Automatic TLS is now a thing" (2024-05-10),
  https://blog.nearlyfreespeech.net/2024/05/10/automatic-tls-is-now-a-thing/ — automatic Let's
  Encrypt for all member sites, nothing to set up and nothing to renew; sites created after
  2024-05-22 get it by default. Vendor-authored, but a blog post rather than documentation.
- **F4** Adding an alias — https://faq.nearlyfreespeech.net/q/addalias — adding an alias while NFSN
  hosts the DNS creates the CNAME automatically. **The exact records for a zone hosted elsewhere are
  not stated on the public FAQ**; NFSN publishes the site's A record values in the Site Information
  panel. Treat "apex via A record from the panel" as **unverified** and confirm in the panel before
  planning a cutover on it.
- **F5** Bare vs www — https://faq.nearlyfreespeech.net/q/yeswww — add both names as aliases and
  enable **canonical name redirection**, which returns a **301 Moved Permanently** from any
  non-canonical alias to the canonical name.

### Bunny.net

- **H1** Pricing — https://bunny.net/pricing/ — CDN **$0.01/GB** North America and Europe (volume
  tiers to $0.002/GB), **no request fees**, **$1 monthly minimum**.
- **H2** Edge Storage — https://bunny.net/storage/ — **$0.01/GB-month** standard (HDD) per region for
  up to two regions, **$0.02/GB-month** edge (SSD); **no API fees, free API egress, no request
  charges**; $1 monthly minimum; no free tier, 14-day trial.
- **H3** Bunny DNS pricing — https://bunny.net/pricing/dns/ — *"Manage up to 500 DNS zones completely
  free"*, unlimited standard and smart queries at no cost, under the same $1 monthly minimum.
- **H4** *(secondary)* SSL for custom domains — https://bunny.net/docs/cdn/ssl-setup — free
  auto-renewing Let's Encrypt certificates per pull-zone hostname, one click to enable; free
  wildcard certificates when the domain is on a Bunny DNS zone. Read via search summary of the
  vendor doc rather than the page itself.
- **H5** *(secondary)* Bunny DNS records — https://bunny.net/docs/dns/records — record types include
  A, AAAA, CAA, CNAME, **Flatten**, MX, NS, PTR, **PullZone**, **Redirect**, SRV, Script, TXT;
  CNAME and PullZone records are **auto-flattened to A/AAAA at the zone apex**, so a root domain can
  point straight at a pull zone, and the Redirect record type gives bare→www directly. Read via
  search summary of the vendor doc.
- **H6** Edge Storage FTP — https://bunny.net/docs/edge-storage-ftp — host `storage.bunnycdn.com`
  (plus regional hosts), **port 21, passive, "Encryption: Not supported"**, username is the storage
  zone name, password auto-generated in the *FTP & API Access* tab; 25 concurrent FTP connections per
  IP, 50 concurrent uploads per zone; the docs call FTP *"outdated and not as secure as newer
  protocols"* and recommend the **HTTP API** instead.

### Measured here, not cited

DNSSEC status for both domains (`dig DS` and `dig DNSKEY` against 8.8.8.8, 2026-10-15 — **neither
domain is signed**, which is what makes the Cloud DNS ALIAS route available). Everything else about
the two sites, their DNS, mail and current host comes from `select-web-hosting/requirements.md`,
which measured it on 2026-10-15.

---

## 9. The recommendations, with the reasoning

### www.f3lcontestseries.org → AWS S3 + CloudFront + ACM, DNS left at Google Cloud DNS

**Cost: about $0.01/month — under $0.15/year.** The only line on the bill is 33.4 MB of S3 storage.

Why it wins:

- **R6 is the deciding requirement, and AWS answers it best.** `aws s3 sync --dryrun` is a
  first-class vendor CLI that does precisely what `deploy/deploy.py` hand-rolls over FTP: compare
  local against live, print the plan, send nothing. The manifest file, the `.uploading` rename, the
  FTP error handling — most of deploy.py's complexity — gets **deleted** rather than ported. The new
  deploy script is a thin wrapper: a sync in dry-run mode by default, `--upload` to perform it, then
  one invalidation.
- **R4 is explicitly satisfied.** John named S3 as acceptable. At $0.01/month on a card already on
  file, with no minimum, no cap, and no prepaid balance to forget, there is nothing to manage.
- **R2 and R3 cost nothing.** ACM public certificates are free and renew themselves for the life of
  the distribution. Bare→www is a small CloudFront Function or a redirect bucket.
- **The apex works with the zone where it is** — the finding in §1. Three DNS records change, the
  MX and SPF records are never touched, and R10 stays free.
- **R12 is a single command.** `aws s3 sync s3://bucket ./local` and the site is in your hands.

What it costs you, honestly:

- **The most setup of any candidate.** Bucket, Origin Access Control, a certificate in **us-east-1**
  specifically, a distribution, the apex redirect, and a 403→404 custom error response for R9. That
  is an afternoon once, and task 3 should write it down step by step.
- **It is the one candidate where a mistake costs money** rather than pausing the site. At this scale
  the exposure is small, but set a billing alarm at $5 and be done.
- **If a new AWS account is used, switch it to the Paid account plan immediately** ([A3](#8-sources)).
  An existing personal account avoids this entirely and is the better starting point.

### Runner-up: GitHub Pages

$0 if the F3L repo becomes public; **$48/year** (GitHub Pro) if it stays private.

The case for it is real and it is almost entirely about simplicity. The repo is already on GitHub.
Deploy is `git push` — nothing new to install, nothing new to credential, and the "plan" is a git
diff that is better than any dry-run printout. The apex story is the best in the whole comparison:
**four A records that work on Google Cloud DNS exactly as it stands**, and GitHub does the bare→www
301 and the Let's Encrypt certificate for both names with no configuration. 33.4 MB sits well inside
the 1 GB limit.

Why it is the runner-up and not the pick:

- **It is not the dry run R6 describes.** Pushing to a branch publishes; there is no connect, compare
  and print step. For a site whose deploy set is 31 files and whose history is in git anyway this is
  a fair trade — but it is a trade, and R6 is a stated requirement.
- **$48/year to keep a club website private is poor value** next to $0.15/year, and the alternative —
  making the repo public — is a separate decision John has not been asked for.
- **The limits are soft and unenforced-until-they-aren't.** 100 GB/month and 10 builds/hour are
  described as soft limits with no stated enforcement, which is fine at this traffic but is not a
  contract.

If John would rather have "push to deploy" than "dry run then upload", this is the better choice and
he should say so — it is a legitimate reading of R4's "easy to manage" against R6's letter.

### www.mcneilco.com → AWS S3 + CloudFront + ACM, in a second AWS account, zone moved to Route 53

**Cost: $0.50/month — $6.12/year**, almost all of it the Route 53 hosted zone.

Why it wins:

- **One mental model across both sites.** Same CLI, same dry run, same deploy script shape, same
  console. That is the real "easy to manage" win (R4) — John learns one thing, and a step worker
  given either site finds the same tooling. Two different hosts means two sets of quirks to
  remember at the exact moments he has forgotten both.
- **R5 gets its best possible answer: a second, separate AWS account.** Separate root identity,
  separate IAM, separate bill, no path from one site's credentials to the other's files. Set against
  what exists today — one document root, one FTP credential, F3L publicly served under the
  mcneilco.com hostname — that is the complete fix, not a partial one.
- **Route 53 is the honest price of Network Solutions having no ALIAS.** The apex has to move
  somewhere that can point at a hostname; $6/year for a zone in the same account as everything else,
  with alias queries to CloudFront free, is the cheapest and simplest of the places it could go.
- **R1 is finally true here.** The three PHP files are already gone in the staging repo. An S3
  bucket cannot execute code even if someone uploads a `.php` file to it — the requirement becomes
  structural rather than a promise.

What it costs you, honestly:

- **The zone move is the riskiest step in this entire migration**, and it is the only reason this is
  not an unqualified recommendation. mcneilco.com's MX records carry live Google Workspace mail.
  Five MX records must be copied verbatim into Route 53 and **verified by resolving them against the
  Route 53 nameservers directly, before the registrar's NS records are changed** — which is the one
  ordering mistake that would take down John's email rather than a website. Task 3 must write that
  as an explicit gated step with a verification command, not a bullet.
- **The 177-file / 131-file payload gap is unresolved** (`requirements.md` §1, §10 item 4). It does
  not change the host choice — no candidate has a limit either number approaches — but it must be
  settled against the staging repo on Mika before a cutover.

### Runner-up: Netlify Free

$0, and it is the runner-up for one strong reason: **it needs no zone move for this domain.** One A
record to 75.2.60.5 and one CNAME to `<project>.netlify.app`, the MX records never touched, the zone
left at Network Solutions exactly as it is. That removes the single highest-consequence step in the
recommended path. Netlify also handles bare→www and the Let's Encrypt certificate automatically, and
`netlify deploy` → inspect the draft URL → `netlify deploy --prod` is arguably a *better* dry run
than printing a plan, because you can click through the staged site before promoting it.

Why it is the runner-up and not the pick:

- **The 300-credit monthly cap is a hard stop that pauses the site.** No overage, no automatic
  recharge, no roll-over. At 15 credits per production deploy and 20 per GB of transfer, this site
  will never come close — but the failure mode is *the site going dark*, on a plan where John is not
  a paying customer and has no claim.
- **Netlify has already moved the floor once**, doubling the credit cost of bandwidth and compute
  while leaving the Free allowance at 300. A free tier that has been re-priced against its users
  once can be re-priced again, and a brochure site nobody is watching is exactly where that gets
  noticed late.
- **It is a second toolchain** for one of two sites, against the one-mental-model argument above.

If John weighs "never touch the Google Workspace MX records" above "one toolchain for both sites",
Netlify is the better choice for mcneilco.com and this should flip. That is a judgement about his own
risk appetite, not something this document can settle for him.

### Why not the others

- **Cloudflare Pages** is the cheapest candidate with no minimum, no cap and no metered bandwidth —
  genuinely $0 forever for both sites, which is better than AWS's $6.25/year. Three things hold it
  back. It requires **both** zones moved to Cloudflare, so it pays R10's mail-migration cost twice
  over where AWS pays it once and GitHub/Netlify not at all. `wrangler` has **no dry run** (R6), and
  needs Node where everything else here needs Python or one binary. And **Direct Upload cannot later
  become a Git integration** — an irreversible choice made before the first deploy. The §2.8
  non-HTML-content question ([D6](#8-sources)) also wants confirming before 32 MB of photographs
  goes on a free plan. Strong candidate; if the §2.8 point confirms clean and John does not mind
  moving both zones, it is a reasonable third place.
- **NearlyFreeSpeech.NET** is the best *spiritual* match to what exists today: a real Unix host,
  SSH, and `rsync -n --delete` as a dry run that is exact. $4/yr for F3L and $19/yr for mcneilco is
  cheap, separate memberships give clean separation, and TLS is automatic and free. Two things keep
  it out of first place. The **prepaid balance is a recurring obligation with a site-down failure
  mode** — two balances, for sites touched a few times a year, is exactly the kind of thing that gets
  forgotten. And the external-DNS apex instructions could not be verified from public documentation
  ([F4](#8-sources)), which for a site whose apex is the whole R3 question is a gap that has to be
  closed in the panel before planning on it. Worth keeping in view if John would rather have a plain
  server than a CDN.
- **Bunny.net** is competent and cheap-but-not-cheapest ($12/yr per account, entirely the minimum;
  $24/yr for the two separate accounts R5 wants). Its apex handling via Bunny DNS PullZone records is
  the most elegant in the comparison. Against it: both zones move, there is **no dry run and no
  deploy CLI** so the deploy script is the most new code of any candidate, and the FTP path that
  would let `deploy/deploy.py` survive nearly unchanged has **"Encryption: Not supported"** — which
  means plaintext credentials over the wire, the one thing worth leaving behind along with the
  shared account.

---

## 10. Open items this comparison could not close

These do not block task 3 (the migration plan), but three of them must be closed before anything is
bought or cut over.

1. **Correct `requirements.md` §6.** It states Google Cloud DNS has no ALIAS/ANAME and builds the
   "apex redirect vs apex origin" argument on that. Cloud DNS has supported ALIAS at the apex for
   public, non-DNSSEC zones for some time ([A6](#8-sources)), and f3lcontestseries.org qualifies.
   The requirement itself (R3) is unaffected; only the §6 commentary is wrong.
2. **Confirm GitHub Pro's price** on github.com/pricing before John pays for it — the page did not
   render a Pro line when read ([C4](#8-sources)). Only matters if the GitHub Pages runner-up is
   chosen *and* the repo stays private.
3. **Confirm Cloudflare's current non-HTML-content terms** ([D6](#8-sources)) if Cloudflare Pages is
   chosen for F3L, which is 99.6% photography.
4. **Confirm NFSN's apex A record values** in the Site Information panel ([F4](#8-sources)) if NFSN
   is chosen — the public FAQ does not state the records for an externally hosted zone.
5. **Settle the mcneilco.com payload** against the staging repo on Mika (177 files / 71 MB) rather
   than the 131-file / 48.5 MB crawl floor. No candidate's limits turn on it; the cutover's
   verification step does.
6. **Which AWS account.** John's existing personal account, or a new one for F3L plus a second new
   one for mcneilco.com? Either satisfies R4 and R5. If any account is new, it must be moved to the
   **Paid account plan** before it hosts anything ([A3](#8-sources)). This is John's to decide at the
   review gate and belongs in task 3's plan as a prerequisite either way.
