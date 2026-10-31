# Output notes — R5S2o7dv (hosting requirements)

Task: write the hosting requirements for both sites, inventory each, commit as `requirements.md`.
Run on Bishop, 2026-10-15.

## Deliverable

- `select-web-hosting/requirements.md` — the requirements document. Sections: sources and what was
  unreachable (§1), F3L inventory (§2), mcneilco.com inventory (§3), the two side by side (§4),
  how they are hosted today (§5), DNS (§6), mail (§7), requirements R1–R12 (§8), the checklist the
  comparison has to fill in (§9), open questions (§10).

## Fallback used

The 2026-10-13 FTP backup and the mcneilco.com staging repo are both on **Mika**; this step ran on
**Bishop** and neither path exists here (`~/Projects/TPG` is absent entirely; `~/Projects` holds
only `claude-workspace`). Searched to depth 6 under `~` and checked `/Volumes` before falling back.
Per the card's instruction, the inventory came from this repo plus the live sites, and §1 says so.

Consequence to carry into task 2: the mcneilco.com totals are crawl-derived (**131 files / 48.5 MB**)
against the card's staging-repo figure of **177 files / 71 MB**. The gap is unlinked files a crawl
cannot reach. §1 and §10 both flag it.

## Things found that were not in the card

These are measurements, not assumptions, and several change the shape of the comparison:

1. **Neither site has working HTTPS.** Both serve a valid-chain `CN=*.bizland.com` wildcard (expires
   2027-02-26) that matches neither domain, so every browser shows a name mismatch. R2 is new
   capability, not a migration.
2. **No bare-to-www redirect exists today**, and no HTTP-to-HTTPS redirect. Bare and www both answer
   200 directly on both sites. The only redirect anywhere is `/stats/` → the bizland control panel,
   which is host plumbing and disappears with the host.
3. **`www.mcneilco.com` is an A record, not a CNAME** — not symmetric with F3L, whose www *is* a
   CNAME. The card does not say this. It affects how the www name is pointed at a CDN.
4. **The whole F3L site is publicly served at `www.mcneilco.com/f3l_series/`** (200, byte-identical
   to `index.html`). The separation R5 asks for fails today in a concrete, observable way, not just
   administratively.
5. **A third pre-existing broken reference on mcneilco.com**, beyond the two in the staging repo
   README: `css/latofonts.css` asks for `css/fonts/Lato-*` (all 72 → 404) while the files actually
   live at `fonts/lato/` (all 72 present, 23.43 MB). No page has ever loaded these fonts. Half the
   site's bytes are unreachable. Raised as open question 1.
6. **`mcneilco.com` publishes no SPF record** despite running Google Workspace — no TXT at the apex
   at all, confirmed against two resolvers. Pre-existing, out of scope, flagged so the migration
   does not get blamed for it.
7. **Neither domain has a CAA record**, so ACM / Let's Encrypt / any host issuer is unblocked.
8. **The live host returns `HTTP 465` to unknown user-agents** — the crawl needed a browser UA.
   Became R11, since it would break a scripted deploy or link checker.
9. **Google Cloud DNS has no ALIAS/ANAME record type**, and both apexes are A records. "Leave DNS in
   place" and "put the apex on a CDN hostname" cannot both hold for F3L. §6 asks the comparison to
   treat *apex redirect* and *apex origin* as separate questions, since R3 only needs a 301.

## Verification done

- F3L deploy set computed by importing `is_deploy_path()`/`collect_deploy_set()` from
  `deploy/deploy.py`, so the inventory matches exactly what the deploy publishes.
- Live-vs-repo spot check on 5 F3L files: all byte-identical.
- Every DNS fact re-checked with `dig` rather than copied from the card; all card facts confirmed,
  with the one correction in item 3 above.
- Three figures were corrected after first draft (image share 99.6% not 95%, 63 external URLs not
  "about 60", 25 files in mcneilco `assets/` not 24).

## Not done, deliberately

Nothing was bought, no account created, no DNS or site file touched. The three broken references and
the missing SPF record were documented, not fixed — they are out of scope for this step and §8 says
so explicitly.

A stale launcher-written fallback hand-off from an earlier failed attempt remains at
`select-web-hosting/step-outputs/R5S2o7dv-handoff.md`. Those three failures were OAuth session
expiry, not anything in the work. It was left in place as the launcher's own record.
