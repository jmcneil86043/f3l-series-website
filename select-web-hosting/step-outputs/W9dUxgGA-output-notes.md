# Output notes — W9dUxgGA (host comparison)

Task: research and compare the candidate static hosts, cite sources with the date read, commit as
`comparison.md` with a recommendation and a runner-up per site. Run on Bishop, 2026-10-15.

## Deliverable

`select-web-hosting/comparison.md`. Sections: the answer first (§1), ruled out rather than scored
(§2), cost at near-zero traffic with every figure derived (§3), R2 certificates (§4), R3 and the DNS
work (§5), R6 scripted deploy with a dry run (§6), R5 separation / admin effort / lock-in (§7),
sources with the date read (§8), the recommendations with reasoning (§9), open items (§10).

Candidates scored: AWS S3+CloudFront+ACM with DNS left in place, the same with Route 53, GitHub
Pages, Cloudflare Pages, Netlify, and two cheap conventional hosts — NearlyFreeSpeech.NET and
bunny.net.

## The picks

| | Recommendation | Runner-up |
|---|---|---|
| www.f3lcontestseries.org | AWS S3 + CloudFront + ACM, DNS left at Google Cloud DNS — ~$0.01/mo | GitHub Pages — $0 public repo / $48/yr private |
| www.mcneilco.com | AWS S3 + CloudFront + ACM, second AWS account, zone moved to Route 53 — $0.50/mo | Netlify Free — $0, needs no zone move |

Both sites on the recommended path: about **$6.25/year**, against **$368.99/year** today.

## Findings that changed the shape of the comparison

1. **Google Cloud DNS *does* support ALIAS records at the zone apex.** `requirements.md` §6 asserts
   it does not and builds its "apex redirect vs apex origin" framing on that. Google's record
   reference lists ALIAS as a Cloud DNS custom record type, apex-only, answering A/AAAA queries;
   conditions are a public zone and DNSSEC off. Checked both apexes with `dig DS` and `dig DNSKEY`
   against 8.8.8.8 — **neither domain is signed**, so F3L qualifies. This removes the main objection
   to AWS for F3L: the apex can point at CloudFront with the zone left exactly where it is. §10 item 1
   of the comparison asks for the §6 commentary to be corrected.
2. **Network Solutions DNS supports no ALIAS, no ANAME and no apex CNAME** — it offers "web
   forwarding" instead, which has no certificate for the bare name. So mcneilco.com's apex cannot
   reach any hostname-addressed host while its zone stays put. That is what costs it the Route 53
   zone, and it is why the two sites get different runners-up.
3. **GitHub Pages is ruled out for www.mcneilco.com on its own prohibited-uses clause**, not on price
   or capability: Pages "is not allowed to be used as a free web-hosting service to run your online
   business … or any other website that is primarily directed at … providing commercial software as
   a service". mcneilco.com is a commercial software vendor's product site. A Pages product policy,
   so GitHub Pro does not buy past it. Ruled out rather than scored, per `requirements.md` §9.
4. **CloudFront now has flat-rate plans** (Free $0 / 1M requests / 100 GB, Pro $15, Business $200,
   Premium $1,000) **alongside** pay-as-you-go, chosen per distribution. The pay-as-you-go
   always-free tier is still 1 TB egress + 10M requests + 2M Function invocations per month. Both
   are $0 at this traffic; the comparison says so rather than picking one.
5. **A new AWS account is now enrolled in a "Free account plan" that expires.** Up to $200 credits,
   6 months or until credits run out, then AWS **suspends the account and you lose access to your
   resources and data** (90 days' retention, then permanent erasure). Any new account created for
   this must be switched to the Paid account plan *before* it hosts anything. An existing personal
   account is unaffected. This is a migration-plan prerequisite, flagged in §3 and §10 item 6.
6. **Netlify's free tier is now a 300-credit monthly hard cap**, not 100 GB/300 build minutes.
   Production deploy 15 credits, bandwidth 20 credits/GB, web requests 2 credits/10k — all from
   Netlify's own pricing page. No overage, no roll-over, no automatic recharge on Free: when credits
   run out Netlify stops credit-consuming activity. Netlify has already doubled the credit cost of
   bandwidth and compute once while leaving the allowance at 300. Neither site comes close to the
   cap, but the failure mode is the site pausing — that is why Netlify is a runner-up, not a pick.
7. **Cloudflare Pages requires the zone on Cloudflare for an apex custom domain** ("that custom
   domain must be a zone on the Cloudflare account"), so it pays R10's mail-migration cost on both
   domains. Also: **Direct Upload cannot later be switched to a Git integration**, an irreversible
   choice made before the first deploy, and `wrangler pages deploy` has **no dry-run flag**.
8. **Bunny Edge Storage FTP has "Encryption: Not supported."** It is the one path that would let
   `deploy/deploy.py` survive nearly unchanged, and it would carry the credential in plaintext — the
   exact thing worth leaving behind with the shared account. Bunny's own docs call FTP outdated and
   point at the HTTP API.
9. **Two AWS gotchas that belong in the migration plan**, not just the comparison: the ACM
   certificate must be issued in **us-east-1** whatever region the bucket is in; and with a REST
   origin plus Origin Access Control a **missing key returns 403, not 404**, so a CloudFront custom
   error response mapping 403→404 is required to satisfy R9.

## Verification done

- Every price and limit read from the vendor's own pricing page or documentation on 2026-10-15.
  Three items could only be had second-hand and are **marked `(secondary)` in §8 with an instruction
  to confirm**: GitHub Pro's $4/month (github.com/pricing rendered no Pro line), Cloudflare's current
  non-HTML-content terms, and the Netlify credit-model rollout dates. Two Bunny docs (SSL setup, DNS
  record types) were read via search summaries of the vendor pages rather than the pages themselves
  and are marked the same way.
- NFSN's external-DNS apex instructions are **not** on the public FAQ. §8 F4 marks the apex A record
  claim unverified and §10 item 4 says to confirm it in the Site Information panel before planning a
  cutover on it. Not papered over.
- DNSSEC checked directly rather than assumed, because the Cloud DNS ALIAS finding depends on it.
- Payload numbers taken from `requirements.md` §4 and recomputed in GiB for the storage lines so the
  AWS and NFSN figures use the same units.
- `deploy/deploy.py` read for the actual dry-run contract (dry run is the default; `--upload`,
  `--delete`, `--force`, `--allow-dirty`, `--verbose`) so §6 grades candidates against what exists
  rather than against a guess.

## Judgement calls worth knowing about

- **Price is deliberately not the deciding factor.** The whole table spans $0–$24/year, under 7% of
  the current account's cost. §3 says so explicitly and points the decision at R3/R6/R5 instead.
  Cloudflare Pages is in fact cheaper than the recommendation ($0 vs $6.25/yr) and is named as a
  reasonable third place; it loses on the dry run, the double zone move and the Direct Upload
  one-way door, not on money.
- **Both recommendations are AWS, for one mental model across two sites.** Each has a named condition
  under which John should flip to the runner-up, and §9 says what it is: for F3L, if he would rather
  have "push to deploy" than "dry run then upload"; for mcneilco.com, if he weighs "never touch the
  Google Workspace MX records" above one toolchain. Those are his calls, and the document says so
  rather than pretending they are settled.
- **The mcneilco.com zone move is called the riskiest step in the whole migration** and §9 tells task
  3 to write it as a gated step with a verification command — resolve the MX records against the
  Route 53 nameservers directly *before* the registrar's NS records change.

## Not done, deliberately

Nothing bought, no account created, no DNS record or site file touched. No decision recorded in the
ledger — choosing the hosts is checklist item 4, John's [needs-you] gate, and this document is the
input to it, not a substitute. The three broken references and the missing SPF record from
`requirements.md` were left alone; §3 notes only that the unreachable Lato fonts are the one place
these payloads show up on a bill at all (about $0.27/yr on NFSN), and leaves the fix to John.

`requirements.md` §6 was **not** edited to correct the Cloud DNS ALIAS claim — amending the previous
task's committed deliverable felt like the wrong call for a worker scoped to one checklist item. The
correction is stated in comparison.md §1 and §10 item 1, where John will read it at the gate.

A stale launcher-written fallback hand-off from the earlier failed attempts at task 1 remains at
`select-web-hosting/step-outputs/R5S2o7dv-handoff.md`. Left in place as the launcher's own record.
