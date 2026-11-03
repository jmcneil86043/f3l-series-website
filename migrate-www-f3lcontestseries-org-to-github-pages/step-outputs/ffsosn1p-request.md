# Request — Design the approach and write the implementation plan

Task: https://trello.com/c/ffsosn1p   Step: https://trello.com/c/aet0F8Yq   Date: 2026-10-15
Task card ID: 6ad111555be7e641a9577498

## Step card (snapshot at launch)

Name: Migrate www.f3lcontestseries.org to GitHub Pages

Description:

> [dpi]
> [project:f3l-series-website]
> [account:john-bishop]
>
> Move the site off the shared iPage/Network Solutions account onto GitHub Pages, per the
> 2026-10-15 ledger line in `decisions/F3L-Series-Web-Site-decisions.md` and
> `select-web-hosting/migration-plan.md` §7 (Plan B) with the gate decisions in §2.5. The repo goes
> public; the site is published from a `gh-pages` branch built by `is_deploy_path()`, never from
> the root of `main`. The zone stays at Google Cloud DNS: four Pages A records at the apex, `www`
> CNAME to `jmcneil86043.github.io`, custom domain set to the www name. `deploy/preview.sh` plus
> `git diff` before the push is the dry run.
>
> Design: the deploy script rewrite (build the publish tree, diff it against `gh-pages` and the
> live site, push; same CLI and flags as today; `deploy/tests` and `deploy/README.md` follow), the
> Pages setup and cutover sequence from §7 with the §11 verification and the §5.2 TTL schedule,
> the §10 site-file cleanups (the `http://` footer links), and the ledger lines marking the
> 2026-09-13/15 FTP decisions superseded. Do not cancel or change anything on the old host; that
> is a separate, later card.

Tasks checklist at launch (3 items):

1. `[ ] Design the approach and write the implementation plan` (this task)
2. `[ ] [needs-you] Make the repo public, set the Pages source to the gh-pages branch and the custom domain to www.f3lcontestseries.org, and lower the apex A and www CNAME TTLs to 300 at Google Cloud DNS`
3. `[ ] [needs-you] Merge the branch into main and push (steprunner-launcher merge-step on Bishop), then confirm the site is live on Pages with HTTPS on both names and the bare name redirecting to www`

Comments: none. Attachments: none.

## Where the cited inputs live

The ledger line and the migration plan the description cites are on the unmerged branch
`origin/step/DJy1ViGr-select-web-hosting`, not on `main` and not in this worktree at launch. They
were read from git (`git show step/DJy1ViGr-select-web-hosting:<path>`) without leaving this
worktree; the design's first implementation task merges that branch in.
