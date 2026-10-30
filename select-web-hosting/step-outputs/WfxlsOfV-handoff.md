# Hand-off: choose a host for each site and record the two choices

## Goal

The step "Select web hosting" compares static-site hosts for two sites and recommends one per site.
It buys nothing, creates no account and changes no DNS record or site file. All three research
documents are now written and committed. The next checklist item is yours: read them, pick a host
per site, and record the two picks.

## Current status

**Checklist items 1–3 are done.** Three documents are committed on this branch:

| Document | What it settles |
|---|---|
| `select-web-hosting/requirements.md` | What each site actually is, and requirements **R1–R12** |
| `select-web-hosting/comparison.md` | Seven candidates scored; a recommendation and a runner-up per site, with sources and the date read |
| `select-web-hosting/migration-plan.md` | Four migration plans — recommendation and runner-up for each site — plus the iPage/PayPal cancellation |

The picks the documents arrive at:

| | Recommendation | Runner-up |
|---|---|---|
| **www.f3lcontestseries.org** | AWS S3 + CloudFront + ACM, zone stays at Google Cloud DNS — ~$0.01/mo | GitHub Pages — $0 public repo / ~$48/yr private |
| **www.mcneilco.com** | AWS S3 + CloudFront + ACM, second AWS account, zone moved to Route 53 — $0.50/mo | Netlify Free — $0, and **no zone move** |

Both recommended: about **$6.25/year**, against **$368.99/year** today.

Nothing has been bought, no account exists, no DNS record has been touched and no site file has
been changed.

## What happened

This session wrote `select-web-hosting/migration-plan.md` — four plans (A: F3L on AWS; B: F3L on
GitHub Pages; C: mcneilco.com on AWS + Route 53; D: mcneilco.com on Netlify), each with the setup
steps only you can do, the deploy script shape, the DNS cutover with TTLs, a verification
checklist, rollback, and the iPage cancellation. Nothing was executed; every command in it is
written to be run later.

Five things found while writing it are worth your attention before you choose:

1. **Moving the `mcneilco.com` zone takes up to 48 hours to undo.** The `.com` parent delegation TTL
   is 172800 s, measured directly. `comparison.md` called that zone move the riskiest step in the
   migration; it did not know the rollback is two days. Every other record change in any plan rolls
   back in five minutes. `f3lcontestseries.org` is on `.org`, whose delegation TTL is 3600 s — an
   hour — so the same risk does not apply to F3L. **This sharpens the Netlify-for-mcneilco.com
   argument considerably** (§5.1, §12.2 of the plan).
2. **It may not be either/or.** Plan C's cutover splits in two: `www.mcneilco.com` can be pointed at
   CloudFront *with the zone still at Network Solutions*, so the canonical name, all the traffic and
   HTTPS go live with a five-minute rollback and the Google Workspace MX records untouched. Only the
   bare domain needs the nameserver move, and it can wait days (§8.2). Conditional on Network
   Solutions' DNS manager allowing a CNAME at `www` — five minutes in its control panel answers
   that, and nobody has checked.
3. **Cancelling the iPage hosting could take `mcneilco.com`'s registration with it.** The domain is
   registered at Network Solutions, expires **2027-06-13**, eleven days before the hosting account's
   ~2027-06-25 renewal — same company, possibly one invoice. R7 says the registration stays. The
   plan makes reading the 2026-06-25 invoice line items a blocking gate before any cancellation
   (§13.2). This is the worst outcome available in the project and it had not been looked at.
4. **If GitHub Pages wins F3L, do not publish from the repo root** — it would put `decisions/` and
   every step folder on the public internet. The plan publishes a `gh-pages` branch built from
   `is_deploy_path()` instead. It also means "make the repo public to get Pages for $0" is a bigger
   decision than it looked: the *website* contains nothing private, the decisions ledger and step
   folders do. Repository visibility and site visibility are separate — a private repo can serve a
   fully public Pages site; the only thing privacy costs is the GitHub Pro subscription (§7.1).
5. **Plan A's apex record is unproven.** `comparison.md` established that Google Cloud DNS supports
   an ALIAS record at the zone apex, and both of its preconditions were re-verified (the zone is
   public; neither domain is DNSSEC-signed). But the record has not been created and the exact
   `gcloud` command has not been run. The plan treats it as a gate with a named fallback — move the
   F3L zone to Route 53 as well, +$0.50/mo, which propagates and rolls back in an hour on `.org`
   (§6.3).

## Files & paths

All paths relative to this worktree.

- Requirements and inventory — `select-web-hosting/requirements.md`
- Host comparison, with sources — `select-web-hosting/comparison.md`
- **Migration plan (this session's deliverable)** — `select-web-hosting/migration-plan.md`
- Output notes for this task — `select-web-hosting/step-outputs/WfxlsOfV-output-notes.md`
- Output notes for the comparison — `select-web-hosting/step-outputs/W9dUxgGA-output-notes.md`
- This hand-off — `select-web-hosting/step-outputs/WfxlsOfV-handoff.md`
- Decisions ledger, where your two choices go — `decisions/F3L-Series-Web-Site-decisions.md`
- Today's deploy script, which the migration replaces — `deploy/deploy.py`, `deploy/README.md`
- Branch — `step/DJy1ViGr-select-web-hosting`

Note the branch is **4 commits behind `origin/main`** (they add `deploy/backup.py`, two ledger lines
and a `README.txt` line). None of them touches a published site file, so nothing in the three
documents is affected — but item 5's merge will be a real merge rather than a fast-forward, and
`deploy/backup.py` is on `origin/main` and not in this worktree.

## Pending checklist items

- **[needs-you] Read `requirements.md`, `comparison.md` and `migration-plan.md`, choose a host for
  each site, and record the two choices as lines in `decisions/F3L-Series-Web-Site-decisions.md`
  (or comment them on the task card for the merge item to write)** — this is the ask below.
- [needs-you] Merge the branch into `main` and push, then create the two migration step cards, one
  per site. `select-web-hosting/migration-plan.md` §16 is written as input to that: one card per
  site, plus a **third, later card** for cancelling the iPage account — it must not be a checklist
  item on either migration card, because it must not be done when those cards are done.

## Open decisions

Two for the gate, and four small ones you can answer in the same pass (`migration-plan.md` §2.1
calls them D1–D6):

- **D1 — host for www.f3lcontestseries.org.** AWS (Plan A) or GitHub Pages (Plan B). The documents
  recommend AWS, on R6: `aws s3 sync --dryrun` is a real connect-and-compare dry run and most of
  `deploy/deploy.py` gets deleted rather than ported. Flip to Pages if you would rather have "push
  to deploy" than "dry run then upload" — and see finding 4 above first.
- **D2 — host for www.mcneilco.com.** AWS + Route 53 (Plan C) or Netlify Free (Plan D). The
  documents recommend AWS for one mental model across both sites; findings 1 and 2 above are the
  case for Netlify, or for Plan C's two-stage cutover. This is a judgement about your own risk
  appetite and neither document can settle it for you.
- **D3** — if AWS: your existing personal account, or new ones? Either satisfies R4 and R5. **Any new
  account must be switched to the Paid account plan before it hosts anything**, or AWS suspends it
  after six months and the data goes with it.
- **D4** — if GitHub Pages: repo public ($0) or private with Pro (~$48/yr, price unconfirmed)?
- **D5** — where the **mcneilco.com source of truth** lives. Today it is a git repo on Mika with no
  remote, so no worker on Bishop and no other machine can deploy that site at all. Recommendation:
  push it to a private GitHub repo under `jmcneil86043`. Plans C and D both stall on this.
- **D6** — the DNS TTL to settle on after cutover. Recommendation: 3600 s, not back to 14400/7200.

## The ask

**Choose a host for www.f3lcontestseries.org and a host for www.mcneilco.com, and record the two
choices.** Either add them as lines under **§ Repo and runtime** in
`decisions/F3L-Series-Web-Site-decisions.md`, or comment them on the task card for the merge item to
write. The ledger's own format is one line per decision — date · decision · why · link. Something
like:

```
- **2026-10-1X · www.f3lcontestseries.org moves to <host>, with <DNS arrangement>; the shared
  FatCow/iPage/Network Solutions account is left behind.** Why: <your reason>.
  → `select-web-hosting/comparison.md`, `select-web-hosting/migration-plan.md`
- **2026-10-1X · www.mcneilco.com moves to <host>, in its own account, with <DNS arrangement>.**
  Why: <your reason>. → same two documents
```

Answering D3–D6 at the same time would be useful — each one blocks a first step in the plan — but
D1 and D2 are what the gate needs.

## How to respond

Feedback goes as a comment on the task card (https://trello.com/c/WfxlsOfV) before its label is
cleared. **You clearing the `🤖 needs you` label yourself is what moves the step** — reopening this
session does not, and an assistant reading this hand-off never clears a label or checks a Tasks box.

If you would rather an assistant wrote the two ledger lines for you, say so in the comment along
with the two choices and the reasons; that is a small edit on this branch and the merge item picks
it up.
