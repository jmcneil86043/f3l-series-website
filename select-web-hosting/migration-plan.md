# Migration plan — www.f3lcontestseries.org and www.mcneilco.com

Written 2026-10-15 for step "Select web hosting" (https://trello.com/c/DJy1ViGr), task WfxlsOfV.

Inputs: `select-web-hosting/requirements.md` (requirement numbers **R1–R12** and its § references are
used here without restating them) and `select-web-hosting/comparison.md` (the picks and the source
citations **A1–H6**).

**Nothing in this document has been done.** No account was created, nothing was bought, no DNS
record was edited and no site file was changed. Every command below is written to be run later, by
John or by a step worker, after John picks a host per site at the review gate (checklist item 4).
The only things this task did were read-only: `dig` queries, `git remote -v` / `git log` /
`git ls-tree`, `gh auth status`, version checks of locally installed CLIs, a `mimetypes` lookup, and
reading this repo. §3, §5.1 and the notes at the end of §10 record what those measured.

---

## 1. How to read this

There are **four plans**, two per site — the recommendation and the runner-up from
`comparison.md` §1:

| Plan | Site | Host | Status |
|---|---|---|---|
| **A** | www.f3lcontestseries.org | AWS S3 + CloudFront + ACM, zone stays at Google Cloud DNS | recommended |
| **B** | www.f3lcontestseries.org | GitHub Pages | runner-up |
| **C** | www.mcneilco.com | AWS S3 + CloudFront + ACM, second AWS account, zone moved to Route 53 | recommended |
| **D** | www.mcneilco.com | Netlify Free, zone stays at Network Solutions | runner-up |

**Exactly one plan per site gets executed.** A and B are alternatives; C and D are alternatives.
Any combination of one from each pair works — the two sites are deliberately independent, which is
the point of R5.

Sections §2–§5 and §10–§14 are **common to all four plans** and should be read first. §13
(cancelling the iPage account and its PayPal billing) applies whichever plans are chosen, and is
the only part of this document with a hard external deadline.

Each plan is written as a sequence of numbered steps with checkboxes. Steps marked **(John)** need a
login, a card, or a decision that a step worker cannot supply. Steps marked **(worker)** can be done
by a step worker in a worktree. Steps marked **GATE** must pass before the next step starts —
they are the places where getting the order wrong does damage rather than just wasting time.

---

## 2. What only John can do

Nothing in §2 can be delegated, and most of it has to happen before any worker step is useful.

### 2.1 Decisions to make at the review gate (checklist item 4)

| # | Decision | Needed by |
|---|---|---|
| **D1** | Host for www.f3lcontestseries.org: Plan A or Plan B | everything |
| **D2** | Host for www.mcneilco.com: Plan C or Plan D | everything |
| **D3** | *If Plan A or C:* which AWS account — the existing personal one, or new ones? (`comparison.md` §10 item 6) | Plan A step 1, Plan C step 1 |
| **D4** | *If Plan B:* does the F3L repo go **public** (so Pages is $0) or stay private with GitHub Pro (~$48/yr, price unconfirmed — `comparison.md` §8 C4)? See §7.1, which found a reason to think twice about public | Plan B step 1 |
| **D5** | Where the **mcneilco.com source of truth** lives. Today it is a git repo on Mika only (`~/Projects/JMCo/mcneilco.com-site`, per the 2026-10-15 card comment) with no remote named anywhere. Neither a worker on Bishop nor a deploy from any other machine can reach it. See §2.3 | Plans C and D, first step |
| **D6** | The new steady-state DNS TTL after cutover. Recommendation: **3600 s**, not back to 14400/7200 — see §5.2 | cutover day |

D1 and D2 are the gate. D3–D6 can be answered in the same pass; they are small.

### 2.2 Accounts, billing and credentials

Per plan. Do these in order within a plan; they are its step 1 in every case.

**Plan A / Plan C (AWS).**

1. Decide D3. If **any new account** is created: immediately move it to the **Paid account plan**,
   before anything is hosted on it. A new AWS account is enrolled in a free *account plan* that
   expires after 6 months or $200 of credits, after which **AWS suspends the account and access to
   its resources and data is lost** (`comparison.md` §3, source A3). This is a five-minute setting
   and skipping it is the one setup mistake in this whole plan that destroys data rather than
   inconveniencing someone.
2. Set a **billing alarm at $5/month** on each account (AWS Budgets, or a CloudWatch billing alarm
   in us-east-1). The expected bill is $0.01/month for F3L and $0.50/month for mcneilco.com; $5 is
   loud enough to be a real signal and quiet enough never to fire by accident.
3. Create a **deploy IAM user per site**, with an access key, scoped to exactly that site's bucket
   plus `cloudfront:CreateInvalidation` on exactly that distribution. Not the root user, not an
   administrator. §4.4 gives the policy shape.
4. Put each access key in the 1Password `automation` vault, as a sibling of the existing
   `F3L Series FTP` item, and copy it into the deploying machine's env file as §4.5 describes.

**Plan B (GitHub Pages).** Answer D4. If the repo stays private, buy GitHub Pro on
`jmcneil86043` — confirm the price on github.com/pricing first (`comparison.md` §10 item 2).
Nothing else needs buying; the account already exists and is already authenticated on Bishop (§3).

**Plan D (Netlify).** Create a Netlify account (free) for mcneilco.com. Do **not** put F3L in the
same account later — one site per account is what keeps R5 true.

**All plans.** Keep the iPage/Network Solutions account and its PayPal billing **exactly as they
are** until §13. The old host staying live and unmodified is the whole rollback story (§12).

### 2.3 DNS and registrar access to confirm before cutover day

These are confirmations, not changes. Each one is a thing the plan assumes and nobody has checked.

- [ ] **(John) Google Cloud DNS.** Which GCP project holds the `f3lcontestseries.org` zone, and does
      John's account have `dns.admin` on it? Needed because the apex **ALIAS record can only be
      created with `gcloud` or the API, not the console** (`comparison.md` §8 A6). Check with
      `gcloud dns managed-zones list`.
- [ ] **(John) Network Solutions.** Login works, and the DNS manager for `mcneilco.com` can (a) edit
      the apex A record, (b) **replace the `www` A record with a CNAME**, and (c) change the
      nameservers. (b) is what makes the safe staging in Plan C step 7 and Plan D step 5 possible;
      Network Solutions' advanced DNS normally allows it, but it has not been verified and both
      plans note the fallback if it does not.
- [ ] **(John) Squarespace Domains.** Login works for `f3lcontestseries.org` (expires 2028-07-02).
      Nothing changes there — the nameservers stay at Google Cloud DNS in both F3L plans — but
      confirm access exists before relying on it in an emergency.
- [ ] **(John) mcneilco.com registration.** It expires **2027-06-13**, eleven days before the
      hosting account's renewal date. §13.2 is explicit about this: the registration must survive
      the hosting cancellation and must be renewed separately. Check now whether the $368.99 invoice
      bundles the registration or bills it separately.

### 2.4 The mcneilco.com source of truth (D5)

Plans C and D both deploy a directory tree. Today that tree exists in exactly one place — a git repo
on Mika with no remote. Before either plan can run anywhere except on Mika, John has to pick one:

- **Push it to a new private GitHub repo** under `jmcneil86043` (e.g. `mcneilco.com-site`). This is
  the recommendation: it matches what F3L already does, it gives the deploy script a commit to
  record, and it makes the site's history reviewable. It is also required if Plan D is ever wired to
  Netlify's git integration rather than CLI deploys.
- **Or deploy only from Mika**, and accept that no step worker on Bishop can ever touch that site.

Either way, settle `comparison.md` §10 item 5 at the same time: the staging repo is **177 files /
71 MB**, the live crawl saw **131 files / 48.5 MB**. The verification in §11 counts objects after
deploy, so the expected number has to be known. `find . -type f -not -path './.git/*' | wc -l` in
the staging repo on Mika settles it in one command.

---

## 3. Tooling, as measured on Bishop today

Checked 2026-10-15 in this worktree. This is what is and is not already installed on the machine
that runs step workers.

| Tool | State on Bishop | Consequence |
|---|---|---|
| `aws` | **installed**, aws-cli/2.36.42 | Plans A and C need no install. `--dryrun` is available |
| AWS credentials | **none configured.** One named profile exists, `nimbus`, belonging to other work | New profiles must be added; **do not reuse or disturb `nimbus`**, and do not make either site's profile the default |
| `gh` | **installed**, 2.93.0, authenticated as `jmcneil86043`, scopes `gist, read:org, repo` | Plan B needs no install and no new auth |
| `git` remote for this repo | `git@github.com:jmcneil86043/f3l-series-website.git`, **private**, default branch `main` | Confirms Plan B's starting point and D4's cost question |
| `netlify` | **not installed** | Plan D runs it as `npx netlify-cli`, or installs it. Node v26.8.2 and `npx` 11.19.1 are present |
| `wrangler` | not installed | only relevant if Cloudflare Pages is revived as a third place |
| `python3` | 3.14.7 | the new deploy script stays Python, as today |
| `op` (1Password CLI) | **installed**, 2.40.0 | **This contradicts the 2026-09-15 ledger line**, which recorded that `op` is not installed on Bishop and that the env file therefore holds the password itself. `op` is here now. §4.5 notes what that changes; it is not a decision this task makes |
| `rsync` | openrsync, protocol 29 | only relevant if NearlyFreeSpeech is revived |

---

## 4. The deploy script (R6), and what happens to `deploy/deploy.py`

### 4.1 The contract that must not change

Whatever replaces it, the new script keeps today's surface exactly, because it is what John, the
`deploy/README.md` acceptance checklist, and any future step worker already know:

```sh
deploy/deploy.py            # dry run: connect, compare, print the plan, change nothing
deploy/deploy.py --upload   # publish
```

| Flag | Meaning, preserved |
|---|---|
| *(no flag)* | **dry run is the default.** Exit 0 |
| `--upload` | perform the plan |
| `--force` | re-send everything |
| `--delete` | also remove remote-only files |
| `--allow-dirty` | permit `--upload` with uncommitted site files |
| `--env PATH` | use this env file |
| `--verbose` | log the underlying operations |

Exit codes stay **0** success (including a dry run), **1** transport failure, **2** usage problem
(missing credential, bad env file, uncommitted site files, missing destination).

The dry run's output keeps its four headings — **New**, **Changed**, **Unchanged**, **Remote-only** —
with totals. That is what makes it a dry run rather than a guess: it connects, reads what is
actually live, and reports the difference.

### 4.2 What survives from today's `deploy.py`, and what gets deleted

`deploy/deploy.py` is 552 lines. Under Plan A roughly half of it is the answer to problems FTP
created, and those lines go.

**Keep, essentially unchanged — this is the valuable half:**

| Lines | What | Why it survives |
|---|---|---|
| `is_deploy_path()`, `collect_deploy_set()`, `DEPLOY_*` constants | the definition of what gets published | the one authoritative answer to "what is the site", used by every plan including Plan B |
| `sha256_file()` | content hashing | still the honest basis for "changed" |
| `Plan`, `compute_plan()`, `print_plan()`, `format_size()` | the dry-run report | the whole point of R6 |
| `git_state()`, `parse_porcelain_z()` | the clean-tree check | `--upload` must still refuse a dirty tree |
| `parse_env_file()`, `load_env_file()`, `resolve_settings()`, `op_read()`, `Settings` | credential handling, env-file precedence, permission warning | unchanged problem, already solved, already tested |
| `build_parser()`, `main()`, exit codes | the CLI contract in §4.1 | unchanged by design |
| `Remote` abstract base (lines 157–181) | the transport seam | **this is why the port is cheap.** `FtpRemote` is one implementation behind it; the new backend is a second |
| `deploy/tests/test_deploy.py`'s fake-server tests | coverage | they test against `Remote`, not against FTP |

**Delete, with the FTP host:**

| Lines | What | Why it goes |
|---|---|---|
| `FtpRemote` (182–277), ~95 lines | ftplib session, passive mode, error translation, `--verbose` command logging | S3 is an HTTP API with a CLI in front of it |
| `UPLOAD_SUFFIX` / the `.uploading` rename dance in `execute_plan()` | atomic publish | **S3 object PUTs are atomic.** A visitor never sees a half-written object. The single cleverest part of today's script becomes dead weight |
| `MANIFEST_NAME` as the *change oracle* (`.f3l-deploy-manifest.json` on the server) | per-file sha256 kept server-side because *"FTP has no checksum command"* (`deploy/README.md`) | **S3 does have one.** See §4.3 |
| `parent_dirs()`, the directory-creation logic, the "won't create the remote dir" guard | FTP needs directories to exist | S3 has no directories; a key with slashes in it is just a key |
| `upload_order()` — assets, then `styles.css`, then pages | partial-deploy safety over a slow serial FTP link | still worth keeping as a **two-pass ordering** so a visitor mid-deploy never gets a new page referencing an asset that has not landed. Cheap to preserve: sync `assets/` and `styles.css` first, `*.html` second |

Keep the manifest as an **audit record** — commit, timestamp, deployer, dirty flag — because it is
useful and `deploy/README.md` advertises it (`curl …/.f3l-deploy-manifest.json`). Just stop asking
it what changed.

### 4.3 Plan A/C: the change oracle, and one trap worth naming

The obvious script is a wrapper around `aws s3 sync ./ s3://bucket --dryrun`. It mostly works, and
the dry run is real — it lists the live bucket and reports what it would do (source A8). But:

> **`aws s3 sync` compares size and modification time, not content.** A git checkout gives every
> file a fresh mtime. On a new clone or worktree, `sync` therefore proposes re-uploading all 31
> files even when the bucket is already identical.

That is harmless as a cost ($0.0002) and fatal as a *report* — the dry run is supposed to tell John
what actually changed, and this one would say "everything, every time from a new worktree". The same
reason the FTP script grew a manifest.

Three ways out, in order of preference:

1. **Compare local MD5 against the S3 ETag.** `aws s3api list-objects-v2` returns `Key`, `Size` and
   `ETag` in one call, and for a single-part upload the ETag *is* the MD5 of the object. The largest
   file on either site is `assets/wagon.jpg` at 6.55 MB, under the AWS CLI's 8 MB multipart
   threshold, so **every object on both sites is single-part** and every ETag is a usable checksum.
   This keeps `compute_plan()` and the four-heading report exactly as they are, needs no server-side
   manifest at all, and is *more* accurate than today (it compares against the live object, not
   against a record of the last deploy). **Recommended.** Guard it: if any ETag comes back with a
   `-N` suffix, that object was multipart — fall back to treating it as changed, and say so in the
   output.
2. `--size-only`. One flag, but it cannot see a same-size edit, and HTML edits that keep the byte
   count are entirely possible.
3. Let it re-upload. Honest, cheap, and makes the dry run useless as a change report.

With option 1 the shape is:

```
dry run:   list-objects-v2  →  compute_plan(local_md5, remote_etag)  →  print_plan()
--upload:  s3 cp / s3 sync the changed set   (assets + styles.css, then *.html)
           →  put the audit manifest
           →  cloudfront create-invalidation --paths "/*"
           →  print the invalidation ID
```

The invalidation is **one path**, and the first 1,000 paths a month are free (source A2). Do not
invalidate per file; `/*` is one path and costs the same as nothing.

Two things the script must set at upload time, because on S3 these are object metadata rather than
server behaviour:

- **`Content-Type`.** The AWS CLI guesses from the extension using Python's `mimetypes`. Checked on
  Bishop 2026-10-15: `F3L contest bulletin template 2026 v1.1.doc` → `application/msword`, and the
  four uppercase-extension assets (`soaring_moon.JPG`, `launch_2.JPG`, `PhxPilots.JPG`,
  `ABQPilots.PNG`) → `image/jpeg` / `image/png`. So the guess is right and
  `comparison.md` §6's warning about `binary/octet-stream` does not bite here. **Verify the served
  header after the first deploy anyway** (§11) — it is one `curl -I`, and R8 is a stated
  requirement.
- **`Cache-Control`.** Nothing forces this, but with no cache headers CloudFront falls back to its
  default TTL and a stale page outlives a deploy. Suggested: `max-age=300` on `*.html`,
  `max-age=86400` on `assets/` and `styles.css`. The `/*` invalidation on every deploy makes even a
  wrong guess self-correcting.

### 4.4 Plan A/C: the deploy IAM policy shape

One user per site, one key, bucket-scoped. Not the root user.

```
s3:ListBucket                on arn:aws:s3:::<bucket>
s3:GetObject, s3:PutObject,
s3:DeleteObject, s3:GetObjectAcl   on arn:aws:s3:::<bucket>/*
cloudfront:CreateInvalidation      on arn:aws:cloudfront::<acct>:distribution/<id>
cloudfront:GetInvalidation         on the same
```

`s3:DeleteObject` is only needed for `--delete`. Leaving it out and dropping `--delete` support is a
defensible tightening; today's script already treats deletion as opt-in.

### 4.5 Plan A/C: credentials on the deploying machine

Keep the pattern the 2026-09-13 and 2026-09-15 ledger lines settled — credentials outside the repo,
in `~/.config/f3l-series-website/deploy.env` at mode 600, sourced from 1Password. Only the variable
names change:

```
F3L_AWS_PROFILE=f3l-site              # or F3L_AWS_ACCESS_KEY_ID / F3L_AWS_SECRET_ACCESS_KEY
F3L_S3_BUCKET=<bucket>
F3L_CLOUDFRONT_DISTRIBUTION_ID=<id>
F3L_AWS_REGION=us-west-2
```

`resolve_settings()` already handles process-env-beats-file-beats-default, the 1Password reference
and the mode warning; it needs a new key list and nothing else. Note from §3 that **`op` is now
installed on Bishop** (2.40.0), so `F3L_AWS_SECRET_ACCESS_KEY_OP_REF=op://automation/...` is
available in a way it was not in September. Whether to use it or keep a plain env file is a small
call for the migration step, not for this plan.

Do not make either site's credentials the machine's **default** AWS profile, and do not touch the
existing `nimbus` profile.

### 4.6 Plan B: what "dry run" means when deploy is `git push`

GitHub Pages has no connect-and-compare step, and `comparison.md` §6 is honest that this is a trade
against R6's letter. The script can still give a real plan, and must, because of a problem §7.1
describes: **the repo root is not the published set.**

Shape — same CLI, same flags, a different backend:

```
dry run:  build the publish tree from is_deploy_path() into a temp dir
          → diff it against the tip of the `gh-pages` branch
          → print the same four headings
          → also fetch the live site's files over HTTPS and compare hashes,
            so "what is live" is measured, not assumed
--upload: commit the publish tree to `gh-pages`, push, print the commit and the Pages build URL
```

`collect_deploy_set()` and `is_deploy_path()` carry over verbatim; `git_state()` and the dirty-tree
guard carry over; only the transport changes. The live-site hash comparison is what preserves the
"connect and compare" property, and it is a dozen lines.

### 4.7 Plan D: Netlify

```
dry run:  npx netlify-cli deploy --dir=<tree>            # draft deploy at its own URL
--upload: npx netlify-cli deploy --dir=<tree> --prod
```

This is arguably better than a printed plan — you can click through the staged site before promoting
it. One caution carried from `comparison.md` §3: **each production deploy costs 15 of the month's
300 free credits.** Draft deploys are cheaper but not free. A site that changes "essentially never"
will not come close; a script that deploys in a loop would.

Keep the wrapper anyway, for the dirty-tree guard, the published-set definition and the audit record.
Do not let `--upload` map to anything other than `--prod`.

---

## 5. Cutover discipline — TTLs, ordering, and verifying before DNS

### 5.1 The DNS facts, re-measured today

`dig` against 8.8.8.8, 2026-10-15, in this worktree. All of `requirements.md` §6 confirmed, plus
three facts it did not record.

| Record | Value | TTL |
|---|---|---|
| `f3lcontestseries.org` A | 65.254.248.183 | **14400** |
| `www.f3lcontestseries.org` CNAME | `f3lcontestseries.org.` | **14400** |
| `f3lcontestseries.org` TXT | `v=spf1 include:mailgun.org ~all` | — |
| `f3lcontestseries.org` NS | `ns-cloud-d{1,2,3,4}.googledomains.com` | — |
| `mcneilco.com` A | 65.254.248.220 | **7200** |
| `www.mcneilco.com` A | 65.254.248.220 | **7200** |
| `mcneilco.com` MX ×5 | `aspmx.l.google.com` (1), `alt1`/`alt2` (5), `alt3`/`alt4` (10) | **3600** |
| `mcneilco.com` TXT, `_dmarc` TXT, CAA | **none** | — |
| `mcneilco.com` NS | `ns75.worldnic.com`, `ns76.worldnic.com` | — |
| DNSSEC, both domains | **unsigned** (no DS, no DNSKEY) | — |

New here, and all three matter:

1. **The `.com` parent delegation TTL for `mcneilco.com` is 172800 s — 48 hours.** Measured against
   `a.gtld-servers.net`. So moving that zone to Route 53 takes up to **two days** to take full
   effect, and **rolling the nameservers back takes up to two days as well**. This is the single
   most important new fact in this document and it shapes Plan C (§8) and §12.
2. **The `.org` delegation TTL for `f3lcontestseries.org` is 3600 s — one hour.** If F3L ever needs a
   zone move (the Plan A fallback in §6.3), its rollback is an hour, not two days.
3. **No extra records found in either zone.** 25 common hostnames were probed per domain (`mail`,
   `ftp`, `webmail`, `cpanel`, `smtp`, `autodiscover`, `_dmarc`, the Google Workspace `calendar` /
   `drive` / `sites` / `docs` CNAMEs, and more) — nothing resolved. `mcneilco.com` has no TXT record
   at all, confirming `requirements.md` §7. **A probe list is not an enumeration**: a zone move
   (Plan C only) must still start from the Network Solutions DNS manager's own record list, exported
   and checked record by record. The probes only mean nothing obvious is hiding.

### 5.2 TTL schedule

Applies to every plan that changes a record, which is all four.

| When | What |
|---|---|
| **T−48 h** | Lower the TTL to **300 s** on *only the records that will change* — F3L: the apex A and the `www` CNAME. mcneilco.com: the apex A and the `www` A. Change nothing else. Touch no MX and no TXT record, ever (R10) |
| **T−24 h** | Confirm the short TTL is being served: `dig +noall +answer @8.8.8.8 www.f3lcontestseries.org` should show 300 or less. The 48-hour wait exists because a resolver that cached the old value at 14400 s can hold it for four hours, and 48 h is comfortably past both domains' old TTLs |
| **T−0** | Cut over (per plan) |
| **T+15 min** | Run the §11 verification against the new host |
| **T+48 h** | If everything holds, raise the changed records to **D6's value — 3600 s recommended**. Not back to 14400/7200: an hour is plenty of caching for a site this size, and it makes the next change (or the next rollback) cheap. 300 s is fine to keep too; it costs nothing at this query volume |

Never lower a TTL and cut over in the same sitting. The wait is the entire benefit.

### 5.3 Ordering rules common to all four plans

1. **Certificate before DNS.** Every plan needs a certificate covering **both** the apex and the
   `www` name, because R3's bare→www redirect has to terminate TLS before it can issue a 301.
2. **Content before DNS.** The new host serves the complete, verified site *before* a single public
   record moves. §5.4 is how you check that with no DNS change at all.
3. **`www` before the apex.** `www` is the canonical name, carries the traffic, and in both F3L
   plans and Plan D it is a record whose rollback is one edit and one TTL. The apex is the awkward
   one everywhere (ALIAS in Plan A, a zone move in Plan C). Move the easy, reversible, important
   record first; verify; then do the awkward one.
4. **Do not enable HSTS during the migration**, and do not let any host be configured to send
   `Strict-Transport-Security` until the site has been stable on it for a week. HSTS is the one
   setting that makes rollback to a plain-HTTP origin impossible for every browser that saw it.
5. **Change nothing on the old host.** Do not delete files, do not edit `.htaccess`, do not cancel
   anything. It is the rollback target until §13.

### 5.4 Verifying the new host before touching DNS

This is the step that makes the whole migration low-risk, and it works for all four plans. Resolve
the hostname yourself, to the new host's address, for one command only:

```sh
# Plan A / C — against the CloudFront distribution
addr=$(dig +short dXXXXXXXX.cloudfront.net | head -1)
curl -sS -o /dev/null -w '%{http_code} %{ssl_verify_result}\n' \
     --resolve "www.f3lcontestseries.org:443:$addr" \
     https://www.f3lcontestseries.org/

# Plan B — against GitHub Pages
curl -sS -o /dev/null -w '%{http_code}\n' \
     --resolve "www.f3lcontestseries.org:443:185.199.108.153" \
     https://www.f3lcontestseries.org/

# Plan D — against Netlify
curl -sS -o /dev/null -w '%{http_code}\n' \
     --resolve "www.mcneilco.com:443:75.2.60.5" \
     https://www.mcneilco.com/
```

`--resolve` sends the real SNI and the real `Host` header, so this tests the certificate and the
host's routing exactly as a browser would — while the public DNS still points at iPage. Run the
**whole** §11 page-and-download checklist this way before cutting over. Every plan below says
"run §11 with `--resolve`" at that point.

---

## 6. Plan A — www.f3lcontestseries.org on AWS S3 + CloudFront + ACM

Recommended (`comparison.md` §9). Zone stays at Google Cloud DNS. ~$0.01/month.

Expected elapsed time: an afternoon of setup, then a 48-hour TTL wait, then a 20-minute cutover.

### 6.1 Setup (no DNS change, nothing public)

1. **(John)** Settle D3, and if the account is new, switch it to the **Paid account plan** first
   (§2.2). Set the $5 billing alarm.
2. **(John)** Create the bucket, in a region near the audience — `us-west-2` is a reasonable default
   for a US-southwest contest series. **Block all public access** and leave it blocked; CloudFront
   will reach it through Origin Access Control, not through public ACLs. Do not enable S3 static
   website hosting on this bucket — the REST endpoint is the one that works with OAC.
3. **(worker)** First upload, before any certificate or distribution exists:
   `aws s3 sync . s3://<bucket> --exclude '*' --include '*.html' --include 'styles.css' --include 'assets/*'`
   — or better, the new deploy script from §4 run with `--upload`, which is the first real test of
   it. Expect **31 objects, 35,018,920 bytes** (`requirements.md` §2.2). Verify the count and total:
   `aws s3 ls --recursive --summarize s3://<bucket>`.
4. **(John)** Request an **ACM public certificate in `us-east-1`** — not the bucket's region;
   CloudFront only reads certificates from us-east-1 (`comparison.md` §4). Names:
   **`www.f3lcontestseries.org` and `f3lcontestseries.org`**, both on the one certificate.
   Choose **DNS validation**.
5. **(John)** Add the ACM validation CNAME to the Google Cloud DNS zone. This is a `_xxxx` record —
   it is not a record anyone resolves for the website, and adding it changes nothing a visitor sees.
   **Leave it in the zone forever**: ACM re-validates through it, and removing it is how a
   self-renewing certificate silently stops renewing.
6. **GATE** — certificate status is **Issued**. `aws acm describe-certificate --region us-east-1
   --certificate-arn <arn> --query 'Certificate.Status'`.
7. **(John)** Create the CloudFront distribution:
   - Origin: the bucket's REST endpoint, with **Origin Access Control**, and apply the generated
     bucket policy.
   - Alternate domain names (CNAMEs): **both** `www.f3lcontestseries.org` and
     `f3lcontestseries.org`.
   - Custom SSL certificate: the one from step 4. SNI (free; a dedicated IP is $600/month —
     source A2).
   - Viewer protocol policy: **Redirect HTTP to HTTPS**.
   - Default root object: **`index.html`**. Checked in this worktree: no page on the site links to a
     directory-style path, so no subdirectory index handling is needed.
   - **Custom error response: 403 → 404**, response page not specified, so CloudFront passes a 404
     through. With a REST origin and OAC, a missing key returns **403 AccessDenied, not 404**; R9
     requires a 404 (`comparison.md` §6).
   - Compress objects automatically: on. It does nothing for the 33 MB of photos and helps the HTML.
8. **(John or worker)** The bare→www 301. Two options from `comparison.md` §5; take the first:
   - **A CloudFront Function on viewer-request** attached to the default behaviour. 2,000,000 free
     invocations/month (source A2), one distribution, one certificate, nothing else to maintain:

     ```js
     function handler(event) {
       var host = event.request.headers.host.value;
       if (host === 'f3lcontestseries.org') {
         return {
           statusCode: 301,
           statusDescription: 'Moved Permanently',
           headers: { location: { value: 'https://www.f3lcontestseries.org' + event.request.uri } }
         };
       }
       return event.request;
     }
     ```

     The site uses no query strings, so dropping them is harmless here; add
     `event.request.querystring` handling if that ever changes.
   - Or a **second distribution** over a redirect-only S3 website-endpoint bucket (source A7). More
     moving parts, a second certificate association, same result.
9. **GATE** — **(worker)** run the whole of §11 against the distribution with `--resolve` (§5.4),
   including the bulletin `.doc` download, its `Content-Type: application/msword`, a missing path
   returning **404 and not 403**, and the two F3XVault iframes on `results.html` not being blocked
   by any `Content-Security-Policy` or `X-Frame-Options` CloudFront might be adding. **Nothing public
   has changed yet.** If anything fails, fix it here, where failing costs nothing.

### 6.2 Cutover

10. **(John)** T−48 h: in Google Cloud DNS, lower **only** these two records to TTL 300 —
    `f3lcontestseries.org` A and `www.f3lcontestseries.org` CNAME. Record the current values first,
    verbatim, somewhere outside the zone (§12 needs them): `A 65.254.248.183` and
    `CNAME f3lcontestseries.org.`
11. **(John)** T−24 h: confirm the short TTL is live (§5.2).
12. **(John)** T−0, **`www` first**: replace the `www` CNAME target —
    `www.f3lcontestseries.org. CNAME dXXXXXXXX.cloudfront.net.`, TTL 300. Leave the apex alone for
    now.
13. **GATE** — `dig +short @8.8.8.8 www.f3lcontestseries.org` shows the CloudFront name, then run
    §11 against the real public name with no `--resolve`. **The site is live on AWS at this point**,
    and the bare name still serves the old host at 200 — which is exactly what it does today, so
    nothing is worse than before.
14. **(John)** The apex. **`gcloud` or the API only — this cannot be done in the console**
    (source A6):

    ```sh
    gcloud dns record-sets create f3lcontestseries.org. \
        --zone=<zone> --type=ALIAS --ttl=300 \
        --rrdatas=dXXXXXXXX.cloudfront.net.
    ```

    Confirm the flag spelling against `gcloud dns record-sets create --help` on the day; the record
    type is documented but this exact invocation has not been run. Delete the old apex A record in
    the same transaction if `gcloud` allows it, otherwise delete it immediately after.
15. **GATE — the one place Plan A can fail outright.** `dig +short @8.8.8.8 f3lcontestseries.org`
    must return CloudFront IPv4 addresses, and `curl -sS -o /dev/null -w '%{http_code}
    %{redirect_url}\n' https://f3lcontestseries.org/` must return `301
    https://www.f3lcontestseries.org/`. If Cloud DNS rejects the ALIAS, or accepts it and does not
    resolve to the distribution, go to §6.3. Do not leave the apex broken while deciding — restore
    `A 65.254.248.183` (it still works; the old host is live) and take the decision calmly.
16. **(John)** T+48 h: raise both records to D6's TTL. Leave the ACM validation CNAME in place.

### 6.3 If the apex ALIAS does not work

`comparison.md` §1 established that Cloud DNS supports ALIAS at the apex for public, unsigned zones,
and both preconditions were re-verified today (§5.1: unsigned, and the zone is public). But the
record has not actually been created, and the whole F3L recommendation rests on it.

**Fallback: move the `f3lcontestseries.org` zone to Route 53**, +$0.50/month, and use an alias A
record to the distribution — the same mechanism Plan C uses for mcneilco.com. It is cheap, known to
work, and **the `.org` delegation TTL is 3600 s** (§5.1), so this zone move propagates in an hour
and rolls back in an hour. F3L's zone carries one TXT record (the Mailgun SPF) and the Mailgun MX
records, which must be copied verbatim and verified against the Route 53 nameservers before the
registrar's NS records change — Plan C step 5 is the procedure, at one tenth the risk because the
parent TTL is 48× shorter and the mail is Mailgun rather than John's own inbox.

Do not fall back to "leave the apex on the old host": that IP dies in §13.

---

## 7. Plan B — www.f3lcontestseries.org on GitHub Pages

Runner-up (`comparison.md` §9). $0 with a public repo, ~$48/yr with GitHub Pro if it stays private.

Simpler than Plan A in every respect except one, which nobody has flagged yet:

### 7.1 The thing to settle before choosing Plan B

**This repo's root is not the published set.** It also contains `decisions/`,
`step-0-design-and-implement-an-ftp-deployment/`, `step-1-schedule-updates-cvrc-dec-5-6/`,
`select-web-hosting/`, `deploy/` and `README.txt`. Publishing from the root of `main` would put the
decisions ledger, every design and risks document, and this migration plan on the public internet at
`www.f3lcontestseries.org/decisions/…`.

That has two consequences:

- **Publish from a `gh-pages` branch built by the deploy script** (§4.6), never from the root of
  `main`. `is_deploy_path()` stays the single definition of what is public, which is the same
  guarantee today's FTP deploy gives. A `/docs` folder or a Jekyll `exclude:` list would also work
  and both are easier to get wrong.
- **D4's "make the repo public" option is bigger than it looks.** It publishes the decisions ledger
  and every step folder as repository content, regardless of what Pages serves. `comparison.md` §9
  says "there is nothing in it that isn't already on the public internet" — that is true of the
  *website*, and not of `decisions/` or the step folders. Note that **repository visibility and site
  visibility are separate** (source C3): a private repo can publish a fully public Pages site. The
  only thing privacy costs is the Pro subscription.

### 7.2 Setup

1. **(John)** Settle D4. If private, buy Pro (confirm the price first).
2. **(worker)** Write the `gh-pages` builder (§4.6) and run its dry run. Build the tree, confirm it
   is **31 files / 35,018,920 bytes** and contains no `decisions/`, no step folder, no `deploy/`, no
   `README.txt`.
3. **(worker)** Add `.nojekyll` to the publish tree. Nothing on this site needs Jekyll, and without
   the file Jekyll will quietly ignore any path beginning with an underscore.
4. **(worker)** Push `gh-pages`. **(John)** In repo Settings → Pages, set the source to that branch,
   and set the custom domain to **`www.f3lcontestseries.org`** — the www name, not the apex. That is
   what makes GitHub serve the apex→www 301 for free (source C1).
5. **GATE** — the site is live at `https://jmcneil86043.github.io/f3l-series-website/` or the
   Pages URL, and §11 passes against it (paths will differ from the final ones; check pages,
   the `.doc` download and the iframes).
6. **(John)** Check the repo has **no other DNS records** pointing at it and that the zone has no
   stray A/AAAA/ALIAS records for these names — extra records are the documented way Pages
   certificate issuance fails (source C5).

### 7.3 Cutover

7. **(John)** T−48 h: lower the apex A and `www` CNAME to TTL 300, recording the current values
   (§6.2 step 10).
8. **(John)** T−0: `www.f3lcontestseries.org. CNAME jmcneil86043.github.io.`, TTL 300.
9. **(John)** The apex: replace `A 65.254.248.183` with the **four A records**
   `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   (source C1), TTL 300. No ALIAS, no `gcloud`, no zone move — **this is Plan B's real advantage over
   Plan A**, and §6.3 never arises.
10. **GATE** — Pages provisions the Let's Encrypt certificate only after DNS resolves correctly, so
    unlike Plan A there is a window (usually minutes, up to an hour) where the name points at Pages
    with no valid certificate. Watch repo Settings → Pages until the certificate appears, **then**
    enable **Enforce HTTPS**. Do not enable it before.
11. **GATE** — run §11 against the public names: all 8 pages, the `.doc` download with its content
    type, `https://f3lcontestseries.org/` → `301 https://www.f3lcontestseries.org/`, a missing path
    → 404.
12. **(John)** T+48 h: raise the TTLs to D6's value.

### 7.4 Notes

- The `CNAME` file GitHub writes into the publish branch is the custom domain. The deploy script
  must preserve it or write it, or the next push removes the custom domain.
- Deploy becomes `git push` to `gh-pages`, with a build step. There is no per-deploy cost and no
  invalidation; Pages' own CDN handles it.

---

## 8. Plan C — www.mcneilco.com on AWS, second account, zone moved to Route 53

Recommended (`comparison.md` §9). $0.50/month, almost all of it the hosted zone.

**This plan contains the riskiest step in the entire migration, and §5.1 made it riskier than
`comparison.md` knew:** moving the zone that carries John's live Google Workspace mail, across a
delegation whose parent TTL is **48 hours**. The plan below is built to make that step both verified
in advance and as small as possible — and the staging in step 7 means the website is already live
and safe before the nameservers move at all.

### 8.1 Setup

1. **(John)** Settle D3 and D5. **A second, separate AWS account** is the point of this plan (R5);
   if it is new, switch it to the **Paid account plan** before anything is hosted on it (§2.2), and
   set the $5 billing alarm.
2. **(John)** Settle the payload count (§2.4) against the staging repo on Mika. The verification in
   step 9 needs the expected number of objects.
3. **(John/worker)** Create the bucket in the second account, public access blocked, and upload the
   staging tree. Expect ~177 objects / ~71 MB, or whatever step 2 established.
4. **(John)** ACM certificate **in us-east-1**, DNS validation, names **`www.mcneilco.com` and
   `mcneilco.com`**.

   > The validation CNAME has to go in whichever zone is authoritative *at the time of validation*.
   > Add it to the **Network Solutions** zone now, and add it again to the Route 53 zone in step 5
   > so renewal keeps working after the move. Having it in both places is correct and harmless.

5. **(John)** Create the **Route 53 hosted zone** for `mcneilco.com` in the second account and build
   it as a faithful copy of the live zone plus the two new records. Start from the Network Solutions
   DNS manager's own record listing, exported — not from §5.1's probe list, which is a spot check
   and not an enumeration.

   | Record | Value in Route 53 |
   |---|---|
   | `mcneilco.com` | **alias A** → the CloudFront distribution (free queries, source A5) |
   | `www.mcneilco.com` | **alias A** or CNAME → the distribution. *Note it is an A record today, not a CNAME* |
   | `mcneilco.com` MX | all five, verbatim: `1 aspmx.l.google.com`, `5 alt1`, `5 alt2`, `10 alt3`, `10 alt4 .aspmx.l.google.com`, TTL 3600 |
   | `_xxxx.mcneilco.com` | the ACM validation CNAME from step 4 |
   | TXT | **none today.** Nothing to copy — and do not add an SPF record here. The missing SPF is a real gap and explicitly out of scope (`requirements.md` §7); adding one mid-migration mixes a mail change into a hosting change |
   | NS, SOA | Route 53 creates these; leave them |
   | anything else in the exported listing | copied verbatim |

6. **GATE — the mail gate. Do not skip, do not reorder, do not do this from memory.** Query the
   Route 53 nameservers **directly, by name**, before the registrar knows they exist, and diff the
   answer against the live one:

   ```sh
   r53ns=$(aws route53 get-hosted-zone --id <zone-id> \
             --query 'DelegationSet.NameServers[0]' --output text)

   dig +noall +answer @"$r53ns"      mcneilco.com MX | sort > /tmp/mx-new
   dig +noall +answer @ns75.worldnic.com mcneilco.com MX | sort > /tmp/mx-old
   diff /tmp/mx-new /tmp/mx-old      # must differ only in TTL, if at all

   # and the same for every other non-website record in the export
   dig +noall +answer @"$r53ns" mcneilco.com TXT
   dig +noall +answer @"$r53ns" www.mcneilco.com A
   ```

   All five MX records, same priorities, same targets. **If the diff shows anything but a TTL
   difference, stop.** A missing MX record here means John's email stops arriving the moment the
   nameservers move, and it stays stopped for as long as it takes him to notice — this is the one
   step in the migration where a mistake takes down mail rather than a website.
7. **(John)** Create the CloudFront distribution exactly as Plan A step 7 — OAC origin, both names
   as alternate domain names, the us-east-1 certificate, redirect HTTP to HTTPS, default root object
   `index.html`, **403 → 404 custom error response**, compression on — plus the bare→www function
   from Plan A step 8 with `mcneilco.com` / `https://www.mcneilco.com` substituted.
8. **GATE** — run §11 against the distribution with `--resolve` (§5.4): all 7 HTML pages, the two
   pages converted from PHP (`contact.html`, `getstarted.html`) with their `mailto:` links intact,
   all **four PDFs** under `tutorials/` downloading with `Content-Type: application/pdf`, a missing
   path → 404, and **no path serving anything belonging to F3L** — `/f3l_series/` must 404, which is
   the concrete end of `requirements.md` §5.2.

### 8.2 Cutover, in two separable moves

The website and the nameservers do not have to move together, and they should not.

**Move 1 — `www`, with the zone still at Network Solutions. Fully reversible in two hours.**

9. **(John)** T−48 h: in the Network Solutions DNS manager, lower the apex A and the `www` A record
   to **TTL 300**. Record both current values: `A 65.254.248.220` for each. Change nothing else, and
   do not touch the MX records.
10. **(John)** T−0: replace the `www.mcneilco.com` **A** record with a **CNAME to
    `dXXXXXXXX.cloudfront.net`**, TTL 300.

    If Network Solutions' DNS manager will not create a CNAME at `www` (§2.3 flags this as
    unconfirmed), skip Move 1 and do `www` and the apex together in Move 2. The staging is a
    risk reduction, not a requirement.
11. **GATE** — `dig +short @8.8.8.8 www.mcneilco.com` shows CloudFront; §11 passes against the real
    public name. **The website is now live on AWS**, with HTTPS, with the zone and all five MX
    records untouched at Network Solutions. The bare name still serves the old host at 200, as it
    does today. Stop here for a few days and let it settle — there is no reason to hurry Move 2.

**Move 2 — the nameservers, for the apex. Slow in both directions.**

12. **(John)** Re-run the step 6 mail gate. The zone may have been edited since; the whole point is
    that the check is current.
13. **(John)** At the **registrar** (Network Solutions, which is both registrar and current DNS
    host — R7 means the *registration* stays there; only the nameserver records change), set the
    nameservers to Route 53's four. **Do not delete the Network Solutions zone.** Leave it intact,
    complete and correct — it is the rollback target, and for up to 48 hours some resolvers will
    still be using it.
14. **The dual-authority window, up to 48 hours.** During it, resolvers that already know the old
    nameservers get the old answers and resolvers that have refreshed get Route 53. Both serve the
    site, because the old host is still live. Two things to expect and not panic about:
    - **The apex is HTTPS-capable only on the Route 53 side.** `https://mcneilco.com/` works for
      some resolvers and name-mismatches for others until the window closes. This is why §5.3 rule 4
      forbids HSTS, and why the canonical `www` name was moved first — `www` works correctly on
      *both* sides throughout.
    - **Mail is unaffected either way**, because both nameserver sets answer MX identically. That is
      what step 6 proved.
15. **GATE** — after 48 hours: `dig +short @8.8.8.8 mcneilco.com NS` returns only the Route 53
    names, `dig +short @8.8.8.8 mcneilco.com MX` returns all five Google records, **send and receive
    a test email**, and `curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n'
    https://mcneilco.com/` returns `301 https://www.mcneilco.com/`. Run §11 once more in full.
16. **(John)** Raise the TTLs on the two website records to D6's value. Leave MX at 3600.

### 8.3 If you would rather not move the zone at all

That is Plan D (§9), and it is a legitimate reading of John's own risk appetite —
`comparison.md` §9 says so explicitly. Plan C's steps 1–11 and Plan D's steps 1–7 are independent;
choosing Plan D after doing Plan C's Move 1 is possible but wasteful. Decide D2 before step 1.

---

## 9. Plan D — www.mcneilco.com on Netlify Free

Runner-up (`comparison.md` §9). $0. **Needs no zone move**, which is its entire argument: the five
Google Workspace MX records are never gone near, and §5.1's 48-hour `.com` delegation TTL never
becomes anybody's problem.

### 9.1 Setup

1. **(John)** Settle D5 (§2.4). Netlify CLI deploys work from any local tree; wiring Netlify's git
   integration needs the repo pushed somewhere Netlify can read.
2. **(John)** Create the Netlify account, and a site/project for mcneilco.com **only**. Keep F3L out
   of it.
3. **(worker)** `npx netlify-cli deploy --dir=<tree>` — a draft deploy at its own URL, which is
   Plan D's dry run (§4.7). Click through it. Then `--prod`.
4. **(John)** Add the custom domain. Assign **either** name and Netlify adds both the apex and the
   `www` subdomain to the site automatically (source E2) — which is what gets both onto one
   certificate and gets the bare→www redirect for free. Set `www.mcneilco.com` as the **primary**
   domain so the redirect runs the right way.
5. **(John)** Add a `_headers` file only if §11 finds a content type wrong. Netlify infers them
   per-request from the extension, so the four PDFs and the `.doc` need nothing.
6. **GATE** — run §11 against the Netlify site with `--resolve` (§5.4). Netlify will not issue the
   Let's Encrypt certificate until DNS points at it (source E3), so at this stage test over the
   `*.netlify.app` URL for content and leave the certificate check to step 9.

### 9.2 Cutover

7. **(John)** T−48 h: lower the apex A and the `www` A record to TTL 300 at Network Solutions,
   recording both current values (`A 65.254.248.220`). Touch nothing else.
8. **(John)** T−0, two record changes and no more:

   | Record | From | To |
   |---|---|---|
   | `www.mcneilco.com` | A 65.254.248.220 | **CNAME → `<project>.netlify.app`** |
   | `mcneilco.com` | A 65.254.248.220 | **A → 75.2.60.5** (source E2) |
   | MX ×5, everything else | — | **untouched** |

   If the DNS manager will not create a CNAME at `www` (§2.3), Netlify's documented alternative is
   an A record to the same apex load-balancer address; confirm the current value in Netlify's own
   DNS instructions panel on the day rather than taking 75.2.60.5 from this document — it is a
   published IP that can change.
9. **GATE** — wait for Netlify to show the certificate as provisioned for **both** names, then run
   §11 against the public names: all 9 pages, all four PDFs, `https://mcneilco.com/` →
   `301 https://www.mcneilco.com/`, a missing path → 404, and `dig MX` unchanged.
10. **(John)** T+48 h: raise the two records to D6's value.

### 9.3 The thing to keep an eye on

Netlify Free is a **300-credit monthly hard cap** with no overage and no roll-over, and its failure
mode is the site pausing (`comparison.md` §3). A production deploy is 15 credits; bandwidth is 20
credits/GB. For a site that changes almost never, the practical rules are: do not script repeated
production deploys, and glance at the credit balance once a quarter. Set a calendar reminder for it —
that is the one recurring obligation Plan D adds and Plan C does not.

---

## 10. Site file changes that belong to the migration

**None of these were made by this task** — the step is research-only and the card says no site file
is touched. They are listed so the migration step does them deliberately rather than discovering
them.

**www.f3lcontestseries.org, in this repo:**

- [ ] **The footer self-link on all 8 pages is `http://www.f3lcontestseries.org`** and two links
      point at `http://www.soarabq.org/` (`requirements.md` §2.4). The footer links should become
      `https://` as part of the cutover — they are navigation, not subresources, so they do not
      block anything, but they send visitors out through cleartext and back. The soarabq links are
      somebody else's site; check whether it serves HTTPS before changing them.
- [ ] `deploy/deploy.py` rewritten per §4, and `deploy/deploy.env.example` updated with the new keys.
- [ ] `deploy/README.md` rewritten: the FTP setup section, the manifest explanation, the
      "Safety" section's plain-FTP warning and the acceptance checklist all describe a host that no
      longer exists. The acceptance checklist in particular should become the new host's.
- [ ] `deploy/tests/test_deploy.py` updated — the fake FTP server becomes a fake S3 (or a fake
      `Remote`), which is what the `Remote` seam was for.
- [ ] Plan B only: `.nojekyll` and the `CNAME` file in the publish tree (§7).
- [ ] `deploy/backup.py` (on `origin/main`, not in this worktree — see §13.1) is FTP-only and becomes
      dead code. Delete it **after** §13.1's final backup, not before.
- [ ] `decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime — the 2026-09-13 and
      2026-09-15 FTP lines describe a dead host. Mark them **superseded** and point forward, per the
      ledger's own rule. Also worth a line that `op` is now installed on Bishop (§3), which the
      2026-09-15 entry says it is not. Work from the version on `origin/main`: it carries two further
      lines (`12f451e`, `b5ef709`) that this branch has not seen.

> **This branch is 4 commits behind `origin/main`.** Checked 2026-10-15. None of the four touches a
> published site file — they add `deploy/backup.py`, two ledger lines and a `README.txt` line — so
> the F3L inventory in `requirements.md` §2.2 (31 files, 35,018,920 bytes) is still accurate against
> `origin/main`, and nothing in this plan changes because of them. It does mean the merge in
> checklist item 5 will be a real merge rather than a fast-forward.

**www.mcneilco.com, in the staging repo:**

- [ ] The three pre-existing broken references from `requirements.md` §3.5 — the missing
      `tutorials/McNeilCoDataViewer.pdf`, the schemeless `www.chemaxon.com` link, and
      `css/latofonts.css` pointing at the wrong font path. All explicitly **out of scope** for this
      step and all worth fixing during the migration, when someone is already looking.
- [ ] `requirements.md` §10 item 1: the Lato fonts decision. 23.4 MB of webfonts no page can load.
      Fix the path or delete them — but decide on purpose rather than copying them to a new host by
      default.
- [ ] A deploy script for that repo, same shape as F3L's (§4), so it has one at all. It has never
      had one; the site was deployed by hand over FTP.

**Both, deliberately not done:** the missing SPF record for mcneilco.com (`requirements.md` §7). It
is a real gap and it is a **mail** change. Do not fold it into a hosting migration — §8.1 step 5
says the same thing. It wants its own card.

---

## 11. Verification checklist

Run the whole thing (a) against the new host with `--resolve` before any DNS change, and (b) against
the public names after cutover. It is the same list both times, which is the point.

Set `base` to the site under test and run:

```sh
# For the pre-DNS run, add to every curl:
#   --resolve "www.f3lcontestseries.org:443:<new-host-addr>"
base=https://www.f3lcontestseries.org

# 1. Every page is 200
for p in index about schedule results postal howto host highstart; do
  printf '%-12s %s\n' "$p" "$(curl -sS -o /dev/null -w '%{http_code}' "$base/$p.html")"
done
# mcneilco.com: index acas acas_docs features getacas partners sales contact getstarted

# 2. The stylesheet and a representative asset
curl -sS -o /dev/null -w 'css   %{http_code} %{content_type}\n' "$base/styles.css"
curl -sS -o /dev/null -w 'jpg   %{http_code} %{content_type}\n' "$base/assets/wagon.jpg"
curl -sS -o /dev/null -w 'JPG   %{http_code} %{content_type}\n' "$base/assets/PhxPilots.JPG"

# 3. R8 — the download, with spaces in its name, must download as application/msword
curl -sS -o /dev/null -w 'doc   %{http_code} %{content_type} %{size_download}\n' \
  "$base/assets/F3L%20contest%20bulletin%20template%202026%20v1.1.doc"
# expect: 200 application/msword 56320
# mcneilco.com: all four tutorials/*.pdf, expect application/pdf and
#   6.74 / 4.00 / 3.50 / 1.74 MB respectively

# 4. R9 — a missing path is a 404, NOT a 403 and NOT a redirect to the home page
curl -sS -o /dev/null -w 'miss  %{http_code}\n' "$base/no-such-page.html"
# expect 404.  403 means the CloudFront 403->404 error response is missing

# 5. R9 — no directory listing
curl -sS -o /dev/null -w 'dir   %{http_code}\n' "$base/assets/"
# expect 403 or 404, never 200 with a file list

# 6. R3 — bare domain 301s to www, over HTTPS
curl -sS -o /dev/null -w 'apex  %{http_code} -> %{redirect_url}\n' https://f3lcontestseries.org/
# expect: 301 -> https://www.f3lcontestseries.org/

# 7. HTTP redirects to HTTPS
curl -sS -o /dev/null -w 'http  %{http_code} -> %{redirect_url}\n' http://www.f3lcontestseries.org/

# 8. R2 — the certificate matches the name and is not the old *.bizland.com
echo | openssl s_client -connect www.f3lcontestseries.org:443 \
         -servername www.f3lcontestseries.org 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
# expect both names in subjectAltName, and an issuer that is not RapidSSL/*.bizland.com

# 9. R10 — mail untouched.  Run before AND after, diff the output
dig +short @8.8.8.8 f3lcontestseries.org MX
dig +short @8.8.8.8 f3lcontestseries.org TXT
# mcneilco.com: all five aspmx records, and TXT still empty

# 10. R11 — a plain client is served.  No user-agent games
curl -sS -A '' -o /dev/null -w 'plain %{http_code}\n' "$base/"
curl -sS -A 'curl-check/1.0' -o /dev/null -w 'ua    %{http_code}\n' "$base/"
# both 200.  The old host returned 465 to unknown agents

# 11. F3L only — the two F3XVault iframes must not be blocked by a new header
curl -sSI "$base/results.html" | grep -iE 'content-security-policy|x-frame-options'
# expect no output, or a policy that permits https://www.f3xvault.com/

# 12. Case sensitivity is unchanged
curl -sS -o /dev/null -w 'case  %{http_code}\n' "$base/Index.html"   # expect 404

# 13. robots.txt still resolves (it is empty, and that is correct)
curl -sS -o /dev/null -w 'robot %{http_code}\n' "$base/robots.txt"
```

Also, by eye and not by curl:

- [ ] Open all 8 (or 9) pages in a browser. Images render, the stylesheet applies, no mixed-content
      warning in the console.
- [ ] F3L: on **Host a Contest**, click the bulletin template link. A `.doc` file downloads, with
      its spaces intact in the saved filename, and Word opens it.
- [ ] F3L: on **Results**, both F3XVault standings iframes render.
- [ ] mcneilco.com: the `mailto:` links on `contact.html` and `getstarted.html` open a composer
      addressed to sales@mcneilco.com — and no `.php` path remains anywhere.
- [ ] mcneilco.com: `https://www.mcneilco.com/f3l_series/` returns **404**. That is R5 made real:
      `requirements.md` §5.2 found the whole F3L site publicly served under this hostname today.
- [ ] Object count and total bytes on the new host match the inventory — F3L **31 objects /
      35,018,920 bytes**; mcneilco.com whatever §2.4 settled.
- [ ] Send and receive one real email on each domain.

---

## 12. Rollback

### 12.1 The reason rollback is easy, and the one thing that would break it

**Until §13 happens, the iPage account is live and unmodified and serving both sites.** Rollback is
therefore: put the DNS records back. Nothing to restore, nothing to re-upload.

This holds only if §5.3 rule 5 is honoured — **change nothing on the old host.** No file deletions,
no `.htaccess` edits, no "tidying up", and above all no cancellation until §13's gates pass.

Write these values down somewhere that is not the zone you are editing, before you edit it:

| Record | Restore to | Current TTL (raise back after) |
|---|---|---|
| `f3lcontestseries.org` | `A 65.254.248.183` | 14400 |
| `www.f3lcontestseries.org` | `CNAME f3lcontestseries.org.` | 14400 |
| `mcneilco.com` | `A 65.254.248.220` | 7200 |
| `www.mcneilco.com` | `A 65.254.248.220` — **an A record, not a CNAME** | 7200 |
| `mcneilco.com` NS (at the registrar) | `ns75.worldnic.com`, `ns76.worldnic.com` | parent TTL **172800** |

### 12.2 How fast each rollback actually is

| What was changed | Rollback | Time to take effect |
|---|---|---|
| F3L `www` CNAME (Plan A step 12, Plan B step 8) | restore the CNAME | **5 minutes**, if the TTL was lowered to 300 as §5.2 says |
| F3L apex (Plan A step 14, Plan B step 9) | restore `A 65.254.248.183`, delete the ALIAS or the four Pages A records | **5 minutes** |
| mcneilco.com `www` and apex at Network Solutions (Plan C Move 1, Plan D step 8) | restore both A records | **5 minutes** |
| **mcneilco.com nameservers (Plan C Move 2)** | set the registrar back to `ns75`/`ns76.worldnic.com`, which still hold the complete original zone | **up to 48 hours** — the `.com` delegation TTL is 172800 s (§5.1) |
| the ACM validation CNAME | leave it. It harms nothing and removing it breaks renewal | — |
| GitHub Pages custom domain | clear it in repo Settings | immediate on their side |
| Netlify custom domain | remove it from the site | immediate on their side |

**Only one row is slow, and it is the only row that touches mail's authority.** Everything Plan C
does before Move 2 is in the 5-minute tier, which is why §8.2 splits the cutover in two. If Move 2
goes wrong in a way that affects mail, the mitigation is not the nameserver rollback — it is that the
Network Solutions zone is still intact and still answering for the resolvers that have it, and that
step 6's gate proved the Route 53 copy is identical. Rolling the delegation back is the last resort,
not the first response.

### 12.3 Deciding to roll back

Roll back if, after cutover: any page 404s that should not, the certificate does not cover both
names, mail stops, or the bulletin/PDF downloads break. Do not roll back for a wrong cache header, a
missing `Cache-Control`, or a content type that needs one flag — fix those forward.

There is no deadline pressure on any of this until §13, and §13 is deliberately scheduled months
later for exactly that reason.

---

## 13. Decommissioning: the iPage account and its PayPal billing

The shared FatCow / iPage / Network Solutions account costs **$368.99/yr**, was **paid 2026-06-25**,
and runs to about **June 2027**. It must be cancelled before it renews. It is also the rollback
target for everything in §12, so it is cancelled **last**, and not early.

### 13.1 Do not cancel until all of these are true

- [ ] Both sites have been live on their new hosts for **at least four weeks** with no rollback.
- [ ] A **fresh, complete FTP backup** has been taken — not the 2026-10-13 one. Use
      `deploy/backup.py`, the same tool that produced the 2026-10-13 archive (177 MB, 1,513 files).
      Verify the file count and that `backup-log.txt` reports no errors.

      > **It is not in this step's worktree.** `deploy/backup.py` is on `origin/main`
      > (commits `a1bbeb3` and `485ce19`, 2026-10-13); this step's branch was cut from a local `main`
      > that is 4 commits behind, so the file is absent here. Run the backup from an up-to-date
      > checkout, not from this worktree. It also means `deploy/backup.py` is a **fifth** file for
      > §10's deploy rewrite to deal with: once FTP is gone it is dead code, and it should be deleted
      > in the same commit that retires `deploy.py`'s FTP backend — but **not before the final backup
      > in this section has been taken and verified.**
- [ ] That backup is **somewhere that is not only Mika**, and has been spot-restored — open a few
      files, confirm the `f3l_series/` and mcneilco.com trees are complete and the four
      `tutorials/*.pdf` are intact and openable.
- [ ] **`Maildir/` has been checked.** The account carries one (`requirements.md` §7). Confirm
      nothing is still delivering into it and nothing anyone wants is sitting in it. Both domains'
      mail is elsewhere — Mailgun and Google Workspace — so this should be empty or stale, but
      "should be" is not a check. Copy it out regardless.
- [ ] **The account has been inventoried for anything nobody has mentioned.** `stats/`,
      `tutorials/`, any database, any additional domain or subdomain, any mailbox, any cron job, any
      other site. The backup covers files; the control panel covers the rest. Anything found needs a
      home before the account dies.
- [ ] **§13.2 has been settled.** This is the one that can go badly wrong.

### 13.2 The domain registration must survive the hosting cancellation

`mcneilco.com` is **registered at Network Solutions and expires 2027-06-13** — eleven days before
the hosting account's renewal date. Network Solutions is both the registrar and, today, the hosting
provider, and quite possibly bills both on the one invoice.

- [ ] **Find out whether the $368.99 includes the `mcneilco.com` registration.** Pull up the
      2026-06-25 invoice and read the line items.
- [ ] If it does: arrange the **registration renewal separately and first**, confirmed in writing,
      before cancelling anything. **R7 says the domains stay where they are registered.** Losing
      `mcneilco.com` to a lapsed registration while trying to cancel a hosting plan would be the
      worst outcome available in this entire project, and it is a plausible one — the dates are
      eleven days apart and the vendor is the same company.
- [ ] Cancel the **hosting plan**, explicitly. Not "the account", if the account also holds the
      registration. If the vendor's UI only offers account-level cancellation, open a support ticket
      that says in writing which service is being cancelled and which is being kept, and keep the
      reply.
- [ ] After cancellation, **re-verify the registration**: `whois mcneilco.com` still shows an expiry
      in the future and Network Solutions as registrar, and the domain is still in John's account.
- [ ] `f3lcontestseries.org` is at **Squarespace Domains, expires 2028-07-02** — a different
      registrar, unaffected by any of this. Nothing to do.

### 13.3 The cancellation sequence

Order matters: cancel the service first, get it in writing, **then** kill the payment method.
Cancelling the PayPal agreement first can leave an unpaid invoice that the vendor pursues; cancelling
the account without killing the agreement can let a charge through anyway.

1. **(John)** Turn **auto-renew off** in the hosting control panel, and screenshot the setting
      showing it off.
2. **(John)** Cancel the **hosting plan** (§13.2), by whatever route the vendor requires — control
      panel, phone, or ticket. Get a **cancellation confirmation with a reference number, in
      email**. Save it.
3. **(John)** Verify the registration is intact (§13.2).
4. **(John)** Only now: cancel the **PayPal billing agreement.** paypal.com → **Settings** →
      **Payments** → **Manage automatic payments** (PayPal has renamed this page more than once;
      look for automatic payments / pre-approved payments / recurring payments). Find the merchant —
      it may appear as **iPage**, **FatCow**, **Network Solutions**, **Endurance International** or
      **Newfold Digital**, so check every plausible entry rather than searching for one name.
      **Cancel** it, and save the confirmation.
5. **(John)** Check whether any **other** automatic payment on that PayPal account belongs to this
      vendor — bundled products (SSL, backups, SiteLock, a second domain) are sometimes separate
      agreements.
6. **(John)** After the next billing date passes, confirm **no charge posted** — PayPal activity and
      the funding card or bank account both.
7. **(John)** Once the account is gone, the old IPs `65.254.248.183` and `65.254.248.220` stop
      serving. §12's rollback story ends here. That is fine by then, and it is why §13.1 exists.

### 13.4 Dates

| Date | What |
|---|---|
| **2027-04-15** | Reminder: start §13.1's checklist. Fresh backup, Maildir, account inventory |
| **2027-05-01** | Settle §13.2 — read the invoice, arrange the registration renewal separately if it is bundled |
| **2027-05-25** | **Cancel.** A month before the ~2027-06-25 renewal. Some hosts want 30 days' notice and most handle a late cancellation badly |
| **2027-06-01** | Verify no renewal charge is pending, and that the PayPal agreement is gone |
| **2027-06-13** | **`mcneilco.com` registration expiry.** Confirm it renewed |
| **2027-07-01** | Final check: nothing charged, both sites still up, `whois` still good |

Put all six in a calendar John actually reads. The 2027-05-25 one is the only hard deadline in this
document; every other date in this plan is a preference.

---

## 14. Effort and sequencing

| Phase | Who | Rough effort |
|---|---|---|
| D1/D2 at the review gate | John | 30 min reading three documents |
| Plan A or B setup (§6.1 / §7.2) | John + worker | an afternoon (A), an hour (B) |
| New deploy script (§4) | worker | half a day including tests |
| F3L cutover (§6.2 / §7.3) | John | 20 min, plus a 48 h TTL wait |
| mcneilco.com source of truth (§2.4) | John | an hour |
| Plan C or D setup (§8.1 / §9.1) | John + worker | an afternoon (C), an hour (D) |
| mcneilco.com Move 1 (§8.2 / §9.2) | John | 20 min, plus a 48 h TTL wait |
| mcneilco.com Move 2 (Plan C only) | John | 20 min, plus a 48 h propagation window |
| Site file cleanups (§10) | worker | half a day |
| §13 decommissioning | John | two hours, spread over April–June 2027 |

**Do the two sites one at a time, F3L first.** It is the site with a repo, a deploy script to
replace, the lower-stakes mail (Mailgun, not John's inbox), a 1-hour delegation TTL instead of 48,
and nobody's business riding on it. Whatever the first migration teaches, mcneilco.com gets the
benefit.

---

## 15. Open items this plan could not close

Carried from `comparison.md` §10 where still open, plus what §5 and §7 added.

1. **D1–D6** (§2.1). John's, at the review gate.
2. **The Cloud DNS apex ALIAS has not actually been created** (§6.3). Both documented preconditions
   re-verified today — public zone, unsigned — but the record is unproven, the exact `gcloud`
   invocation is unrun, and Plan A's apex depends on it. The fallback (Route 53 for the F3L zone too)
   is cheap, and the `.org` delegation TTL of 3600 s makes it low-risk.
3. **Whether Network Solutions' DNS manager will create a CNAME at `www`** (§2.3). If it will,
   Plan C's cutover splits in two and Plan D is two records. If it will not, both get slightly
   clumsier. Five minutes in the control panel answers it.
4. **GitHub Pro's price** (`comparison.md` §10 item 2), only if Plan B is chosen and the repo stays
   private.
5. **The mcneilco.com payload count** — 177 files / 71 MB versus the 131 / 48.5 MB crawl floor
   (§2.4). One command on Mika.
6. **Whether the $368.99 invoice bundles the `mcneilco.com` registration** (§13.2). This one is not
   optional and nobody has looked.
7. **`requirements.md` §6 still carries the incorrect "Cloud DNS has no ALIAS" statement**
   (`comparison.md` §10 item 1). Both later documents correct it in place; the original has
   deliberately not been edited by either follower task.

---

## 16. What the two migration step cards should contain

Checklist item 5 on the step card creates them. No checklist items are requested from the runner by
this task — item 5 already covers it. Suggested shape, one card per site, so that whichever plan
John picked is the one written down:

**"Migrate www.f3lcontestseries.org to \<chosen host\>"** — §2 prerequisites; the deploy script
rewrite (§4, with `deploy/deploy.py` and its tests and README as the deliverable); §6 or §7 setup to
its pre-DNS gate; the §11 verification run with `--resolve`; the TTL drop and cutover; the §10 F3L
site-file cleanups; the ledger lines in §10 marking the FTP decisions superseded.

**"Migrate www.mcneilco.com to \<chosen host\>"** — §2.4's source-of-truth decision and the payload
count first, because nothing else can start without them; §8 or §9 setup to its pre-DNS gate; the
§11 verification run; the cutover (two moves if Plan C); the §10 staging-repo cleanups; a deploy
script for that repo, which has never had one.

**§13 belongs on neither.** It is a third, later card — *"Cancel the iPage hosting account and its
PayPal billing"* — gated on both migrations being four weeks stable, with the 2027-05-25 deadline on
it and §13.2's registration warning in its description. It must not be a checklist item on either
migration card, because it must not be done when those cards are done.
