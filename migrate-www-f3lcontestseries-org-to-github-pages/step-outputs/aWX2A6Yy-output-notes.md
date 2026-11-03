# Output notes — task aWX2A6Yy (verify.sh, https footer links, Pages docs)

**Task:** Add `deploy/verify.sh` (migration plan §11 with `--resolve`), switch the eight
footer self-links to `https://`, rewrite `deploy/README.md` and `deploy/deploy.env.example`
for Pages, update the `README.txt` line.

**Status:** done — committed as `204adbd` on this step branch. Not pushed, not merged —
those belong to the later `[needs-you]` gate.

## What was done

- **`deploy/verify.sh`** (new, executable, POSIX sh): the §11 checklist, numbered 1-13,
  one line per check (`ok` / `FAIL` / `info` / `skip`), exit 0 if nothing failed, 1 if any
  failed, 2 on bad usage. Three modes:
  - **public** (default): `https://www.f3lcontestseries.org`, TLS verified, all 13 judged.
  - **`--resolve ADDR`** (pre-DNS): the www name forced at a Pages address via
    `curl -k --resolve` (real SNI and Host, so routing is tested as a browser would see
    it). Checks 1-5 and 10-13 judged; 6-7 skipped (the public names still point at the old
    host); 8 reported for the eye, not judged — Pages provisions the Let's Encrypt cert
    only *after* DNS resolves to it, so it can't be judged pre-cutover.
  - **`--base URL`**: any other base (a fork's github.io URL, the old host). 6-8 judged
    only when the base host is the real www or apex name. `--resolve` + `--base` together
    is a usage error.
  - Check 8 requires the SAN to cover **both** `www.f3lcontestseries.org` and
    `f3lcontestseries.org` and the issuer to not be RapidSSL. Check 13 (added by the
    design, not in §11) probes `decisions/`, `deploy/`, `README.txt` and one step folder
    for 404. `robots.txt` is reported as `info`, not judged. Check 9 runs `dig` against
    8.8.8.8 and prints MX/TXT for a before/after diff (`info`; skipped if dig is missing).
- **The eight footer self-links** (`index about schedule results postal howto host
  highstart`, one per file — verified by grep before and after): the footer
  `href="http://www.f3lcontestseries.org"` is now `https://`. The two
  `http://www.soarabq.org/` links stay, per the design (that host's certificate is for
  another name).
- **`deploy/README.md`** rewritten for Pages: the three tools, the dry-run headings
  (New/Changed/Unchanged/Remote-only + `Last deploy:` from the tip's trailers), the
  informational live check, flags and exit codes, what gets published (31 files +
  `.nojekyll` + `CNAME` written on every push), the four optional no-secret settings
  (with a note that the old FTP env file is ignored and may be deleted), "what is live"
  (`git log origin/gh-pages` + the Deployments page), the Pages/DNS setup that must stay
  (public repo, gh-pages-branch source, custom domain www, Enforce HTTPS, the four apex
  A records, the www CNAME, TTL schedule, MX/TXT never touched), the safety list,
  verify.sh usage, and a Pages acceptance checklist replacing the FTP one. The Preview
  section (including the Bishop SSH port-forward) is kept verbatim.
- **`deploy/deploy.env.example`** rewritten: the four `F3L_PAGES_*`/`F3L_SITE_*` keys, all
  commented out (all optional, no secret).
- **`README.txt`**: the "Preview and Deploy" paragraph now names `deploy/deploy.py` as the
  GitHub Pages publisher and `deploy/verify.sh` as the §11 checker; `deploy/backup.py` is
  now described as the old-FTP-account safety copy.

## Evidence

`sh -n` clean; `-h` exits 0; unknown flag, `--resolve` without a value, and
`--resolve` + `--base` together all exit 2.

**Old-host run (the design-mandated proof that the script itself works):**

```
$ deploy/verify.sh --base http://www.f3lcontestseries.org     # exit 1
ok   1   all 8 pages 200
ok   2   styles.css text/css, assets/wagon.jpg image/jpeg, assets/PhxPilots.JPG image/jpeg
ok   3   bulletin 200 application/msword 56320 bytes
ok   4   missing path is a 404
ok   5   assets/ has no directory listing (403)
FAIL 6   apex … SSL: no alternative certificate subject name matches 'f3lcontestseries.org'
FAIL 7   http://www.f3lcontestseries.org/ 200 text/html (want a redirect to https://…)
FAIL 8   certificate wrong (SAN www=no apex=no rapidssl=yes): subject=CN=*.bizland.com
         issuer=… CN=RapidSSL TLS RSA CA G1 … DNS:*.bizland.com, DNS:bizland.com
info 9   mail records: MX 10 mxb.mailgun.org. 10 mxa.mailgun.org. | TXT "v=spf1 include:mailgun.org ~all"
FAIL 10  user agents: plain=465 custom=200 (want 200 200)
ok   11  no CSP or X-Frame-Options blocks the F3XVault iframes
ok   12  Index.html is a 404 (case sensitivity intact)
FAIL 13  reachable where they must be 404: README.txt(200 text/plain)
info     robots.txt 200 (404 is correct on Pages; 200+empty is what the old host does)
12 checks: 7 ok, 5 failed, 0 skipped
```

The design predicted checks 6-8 would fail "on the old host" — they do (the bizland.com
certificate, no apex 301, no http→https redirect). Two more checks also fail, and both
are true findings about the old host, not script bugs: check 10 shows the old host
returning **465 for the plain user agent** (R11's user-agent games, live-confirmed) while
serving the custom one; check 13 shows a stray `README.txt` at the old web root (200
text/plain) that the publish tree must not contain — and doesn't, per task 1's `git
ls-tree`-based oracle. Every FAIL names the wrong value and the wanted one, which is the
point of the run.

**`--resolve` smoke run against a Pages address** (expected to fail on content — gh-pages
isn't published yet; the first `--upload` is the Closing task):

```
$ deploy/verify.sh --resolve 185.199.108.153     # exit 1
FAIL 1   pages not 200: index.html(404 …) …   (all 8, nothing built yet)
FAIL 2   stylesheet/assets wrong: styles.css(404) …
FAIL 3   bulletin 404 …
ok   4   missing path is a 404
ok   5   assets/ has no directory listing (404)
skip 6   apex -> www 301  (pre-DNS: the public names still point at the old host)
skip 7   http -> https  (pre-DNS: …)
info 8   certificate presented at 185.199.108.153 (for the eye, not judged):
         subject=CN=*.github.io issuer=Let's Encrypt …
info 9   mail records: (unchanged)
FAIL 10  user agents: plain=404 custom=404
FAIL 11  content-security-policy: default-src 'none' … does not allow the F3XVault iframes
ok   12  Index.html is a 404
ok   13  decisions/, deploy/, README.txt and a step folder are all 404
info     robots.txt 404
11 checks: 4 ok, 5 failed, 2 skipped
```

The plumbing is proven: the forced-SNI fetches reach Pages, 6-7 skip with the reason, 8
reports the pre-DNS `*.github.io` Let's Encrypt cert for the eye, and Pages' own 404
behaviour satisfies 4/5/12/13. (Check 11's FAIL here is the *404 page's* CSP header —
once real content is served, `results.html` is our page and the check re-measures.)

**Test suite** (deploy.py untouched by this task; confirmed still green):

```
$ python3 -m unittest discover -s deploy/tests
Ran 50 tests in 4.539s
OK
```

## Flag for the later old-host work

`deploy/backup.py` is **out of sync** with the rewritten `deploy.py`: it imports
`deploy.FTP_TIMEOUT` and uses `settings.host`/`settings.user`/`settings.password`, all
removed in task 1's rewrite (it now fails at runtime with `AttributeError`). It was left
untouched deliberately — the spec keeps it for the §13.1 final pre-decommissioning backup
of the old FTP account. The later old-host/decommissioning card must update it (point it
back at the FTP settings it needs) before it can run. The new `deploy/README.md` says so
in its "Safety copy of the old FTP account" section.

## For the Closing task and the two gates

- The **first `--upload`** (Closing) will create `gh-pages` and push 31 files +
  `.nojekyll` + `CNAME`; after it, `deploy/verify.sh --resolve <one of the four Pages
  addresses>` should pass all judged content checks (1-5, 10-13) — that is the pre-DNS
  gate's proof.
- After the **DNS cutover gate**, `deploy/verify.sh` (no arguments, public run) should
  pass all 13 checks once Pages' certificate has been provisioned; check 9's MX/TXT line
  is for diffing against the pre-cutover run (capture one of each).
- Remember `--resolve` reports check 8 as `info`, not judged — by design, the certificate
  cannot exist pre-cutover.
