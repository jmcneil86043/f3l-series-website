# Output notes — WfxlsOfV (migration plan)

Task: draft the migration plan for each site under its recommended host and its runner-up — the
account and setup steps John must do himself, the deploy script shape (dry run first, replacing
`deploy/deploy.py` for F3L), DNS cutover with record TTLs, verification checks, rollback, and
cancelling the iPage account and its PayPal billing before June 2027. No account created, nothing
bought, no DNS or site file touched. Commit as `migration-plan.md`. Run on Bishop, 2026-10-15.

## Deliverable

`select-web-hosting/migration-plan.md`. Four plans, two per site, from `comparison.md` §1:

| Plan | Site | Host |
|---|---|---|
| **A** | www.f3lcontestseries.org | AWS S3 + CloudFront + ACM, zone stays at Google Cloud DNS *(recommended)* |
| **B** | www.f3lcontestseries.org | GitHub Pages *(runner-up)* |
| **C** | www.mcneilco.com | AWS, second account, zone moved to Route 53 *(recommended)* |
| **D** | www.mcneilco.com | Netlify Free, zone stays at Network Solutions *(runner-up)* |

Sections: how to read it (§1), what only John can do including six decisions D1–D6 (§2), tooling as
measured on Bishop (§3), the deploy script and what dies in `deploy.py` (§4), cutover discipline —
TTLs, ordering, verifying before DNS (§5), the four plans (§6–§9), site file changes the migration
owes (§10), the verification checklist as runnable commands (§11), rollback with per-record
timings (§12), decommissioning iPage and PayPal (§13), effort (§14), open items (§15), and what the
two migration step cards should contain (§16).

Every requirement citation is `requirements.md`'s R1–R12; every price/limit citation is
`comparison.md`'s A1–H6. Nothing was re-researched from vendors — this task is the plan, not the
comparison.

## Findings this task added, measured rather than inherited

1. **The `.com` parent delegation TTL for `mcneilco.com` is 172800 s — 48 hours.** Measured against
   `a.gtld-servers.net`. So Plan C's zone move takes up to two days to take effect **and up to two
   days to roll back**. `comparison.md` called the zone move the riskiest step without knowing how
   slow its rollback is. This is the single most consequential new fact in the plan.
   By contrast the `.org` delegation for `f3lcontestseries.org` is **3600 s**, which is what makes
   Plan A's fallback (§6.3, move the F3L zone to Route 53 too) a cheap, low-risk option.
2. **Plan C's cutover splits into two separable moves, and should.** `www.mcneilco.com` can be
   CNAME'd to CloudFront *with the zone still at Network Solutions* — the canonical name, all the
   traffic and HTTPS go live with a 5-minute rollback, MX untouched. Only the apex needs the
   nameserver change, and it can wait days. Conditional on Network Solutions' DNS manager allowing a
   CNAME at `www`, which is unverified and flagged (§2.3, §15 item 3).
3. **`aws s3 sync --dryrun` is not a safe change oracle here.** It compares size and mtime; a git
   checkout gives fresh mtimes, so from a new worktree it proposes re-uploading all 31 files even
   when the bucket is identical — the same problem that made `deploy.py` grow a server-side
   manifest. §4.3 recommends comparing local MD5 against the **S3 ETag** from
   `list-objects-v2` instead: every object on both sites is under the CLI's 8 MB multipart threshold
   (largest is `assets/wagon.jpg`, 6.55 MB), so every ETag is a usable MD5. That keeps
   `compute_plan()` and the four-heading report verbatim, needs no manifest, and is *more* accurate
   than today. Guard: treat a `-N` suffixed ETag as changed.
4. **Publishing GitHub Pages from the repo root would publish `decisions/` and every step folder.**
   Plan B therefore publishes a `gh-pages` branch built by `is_deploy_path()`, never the root of
   `main` (§7.1). This also makes D4 ("make the repo public") a bigger decision than `comparison.md`
   §9 treated it: the website contains nothing private, the decisions ledger and step folders do.
   Repository visibility and site visibility are separate (source C3) — a private repo can serve a
   fully public Pages site.
5. **Cancelling the iPage hosting could endanger the `mcneilco.com` registration** (§13.2). The
   domain is registered at Network Solutions, expires **2027-06-13**, eleven days before the hosting
   account's ~2027-06-25 renewal, and the same company bills both — quite possibly on one invoice.
   R7 says the registration stays. The plan makes reading the 2026-06-25 invoice line items a
   blocking gate before any cancellation, and re-verifying `whois` afterwards. This is the worst
   available outcome in the project and nobody had looked at it.
6. **Cancellation order matters:** auto-renew off → cancel the hosting plan and get written
   confirmation → verify the registration → *then* cancel the PayPal agreement. Killing the PayPal
   agreement first can leave an invoice the vendor pursues; cancelling the account without killing
   the agreement can let a charge through. The merchant may appear in PayPal as iPage, FatCow,
   Network Solutions, Endurance International or Newfold Digital — §13.3 says check every entry.
7. **The content-type worry in `comparison.md` §6 does not bite.** Checked Python's `mimetypes` on
   Bishop: `F3L contest bulletin template 2026 v1.1.doc` → `application/msword`, and the four
   uppercase-extension assets (`soaring_moon.JPG`, `launch_2.JPG`, `PhxPilots.JPG`, `ABQPilots.PNG`)
   → correct image types. The AWS CLI uses the same guesser. §11 verifies the served header anyway.
8. **No internal link on the F3L site uses a directory-style path**, so CloudFront needs only a
   default root object at `/` and no subdirectory-index workaround.
9. **No extra records in either zone.** 25 common hostnames probed per domain (mail, ftp, webmail,
   cpanel, autodiscover, `_dmarc`, the Google Workspace `calendar`/`drive`/`sites`/`docs` CNAMEs,
   …) — nothing resolved; `mcneilco.com` has no TXT at all. The plan says explicitly that **a probe
   list is not an enumeration** and Plan C's zone copy must start from Network Solutions' own
   exported record list.
10. **Tooling on Bishop, measured:** `aws` 2.36.42 installed with **no credentials configured** and
    one unrelated profile `nimbus` (don't disturb it, don't become the default); `gh` 2.93.0
    authenticated as `jmcneil86043`; the repo is **private**, default branch `main`; `netlify` and
    `wrangler` absent but `npx`/node present; **`op` 2.40.0 is installed** — which contradicts the
    2026-09-15 ledger line saying it is not, and reopens the 1Password-reference option for
    credentials.
11. **`deploy/backup.py` is on `origin/main` but not in this worktree**, which is 4 commits behind
    `origin/main`. None of those 4 touches a published site file, so `requirements.md` §2.2's
    inventory (31 files / 35,018,920 bytes) still holds against `origin/main`. Two consequences in
    the plan: §13.1's final backup must run from an up-to-date checkout, and §10 adds `backup.py` to
    the files the deploy rewrite retires — after the final backup, not before. Also means item 5's
    merge is a real merge, not a fast-forward.

## Judgement calls worth knowing about

- **Both recommended plans are written to be verifiable before any DNS change.** §5.4's
  `curl --resolve` technique runs the entire §11 checklist against the new host while public DNS
  still points at iPage. Every plan's last pre-cutover step is "run §11 with `--resolve`". This is
  what reduces all four cutovers to a record edit with a known-good target.
- **`www` before the apex, in every plan.** The canonical name carries the traffic and is the
  reversible record everywhere; the apex is the awkward one in three of four plans. Moving the
  important-but-easy record first means the site is live and verified on the new host before anyone
  attempts the awkward one, and an apex failure leaves the bare name serving the old host at 200 —
  exactly what it does today.
- **No HSTS during the migration** (§5.3 rule 5). It is the one setting that makes rollback
  impossible for every browser that saw it.
- **"Change nothing on the old host"** is stated as a rule, not advice: the old account staying live
  and untouched *is* the rollback plan, and that is why §13 is scheduled for April–June 2027 rather
  than as soon as the sites are up.
- **Plan A's apex ALIAS is called out as unproven.** `comparison.md` established Cloud DNS supports
  it and both preconditions were re-verified today (public zone, unsigned — no DS, no DNSKEY), but
  the record has not been created and the exact `gcloud` invocation has not been run. §6.3 names the
  fallback rather than leaving a hole in the recommended path.
- **F3L first, mcneilco.com second** (§14): it has the repo, the script to replace, the lower-stakes
  mail, a 1-hour delegation TTL instead of 48, and no business riding on it.
- **The decommissioning card is deliberately a third card** (§16), not a checklist item on either
  migration card — because it must *not* be done when those cards are done.

## Verification done

- Every DNS fact in `requirements.md` §6 re-measured with `dig` against 8.8.8.8 today and confirmed;
  three facts added that it did not record (both parent delegation TTLs, the MX TTL of 3600, and the
  absence of TXT/DMARC/CAA on mcneilco.com).
- DNSSEC re-checked on both apexes (`DS`, `DNSKEY` — both unsigned), because Plan A's apex depends
  on it.
- `deploy/deploy.py` read function by function to write §4.2's keep/delete table against real line
  ranges rather than a guess. The `Remote` abstract base at lines 157–181 is why the port is cheap —
  `FtpRemote` is one implementation behind a seam, and the tests test the seam.
- Installed-tool versions and auth state checked directly on Bishop (§3), not assumed.
- Repo visibility, default branch and remote read via `gh`/`git`.
- `mimetypes` run locally on the real filenames for the R8 content-type question.
- Branch divergence from `origin/main` checked, and the 4 commits' diffstat read to confirm the
  published-set inventory is unaffected.

## Not done, deliberately

Nothing bought, no account created, no DNS record edited, no site file changed, nothing deployed.
No `requirements.md` or `comparison.md` edits — including the `requirements.md` §6 Cloud DNS error,
left alone for the same reason the previous worker left it (`comparison.md` §10 item 1 and this
plan's §15 item 7 both record it where John will read it).

No `checklist_items_to_add` requested: checklist item 5 already creates the two migration step
cards, and §16 of the plan is written as input to that rather than as a request to the runner.

The three broken mcneilco.com references, the missing SPF record and the unreachable Lato fonts stay
out of scope — §10 lists them as migration-time cleanups and says explicitly that the SPF record is
a mail change that must not be folded into a hosting migration.
