#!/bin/sh
# Verify the F3L Contest Series site against the migration plan's §11 list
# (select-web-hosting/migration-plan.md). One line per check:
# ok / FAIL / info / skip. Exit 0 if nothing failed, 1 if any check failed,
# 2 on bad usage.
#
# Usage:
#   deploy/verify.sh                            public run, after the DNS
#                                               cutover: all 13 checks judged
#   deploy/verify.sh --resolve 185.199.108.153  pre-DNS run: the www name forced
#                                               at a Pages address (real SNI and
#                                               Host, so routing is tested as a
#                                               browser would see it). Checks
#                                               1-5 and 10-13 judged; 6-7
#                                               skipped (the public names still
#                                               point at the old host); 8
#                                               reported for the eye, because
#                                               the certificate is not issued
#                                               until DNS points at Pages
#   deploy/verify.sh --base URL                 another base: a fork's
#                                               github.io URL, or the old host.
#                                               Checks 6-8 are judged only when
#                                               the base is the real name
#   deploy/verify.sh -h                         this help
#
# Needs curl, openssl and dig. Nothing else.

set -u

REAL_WWW=www.f3lcontestseries.org
REAL_APEX=f3lcontestseries.org
DOCS='assets/F3L%20contest%20bulletin%20template%202026%20v1.1.doc'
DOCS_SIZE=56320

n_ok=0
n_fail=0
n_skip=0

ok()   { n_ok=$((n_ok + 1));     printf 'ok   %s\n' "$1"; }
fail() { n_fail=$((n_fail + 1)); printf 'FAIL %s\n' "$1"; }
skip() { n_skip=$((n_skip + 1)); printf 'skip %s\n' "$1"; }
info() { printf 'info %s\n' "$1"; }

usage() {
  sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'
}

MODE=public
BASE="https://$REAL_WWW"
RESOLVE_ADDR=

while [ $# -gt 0 ]; do
  case $1 in
    -h|--help)
      usage
      exit 0
      ;;
    --resolve)
      [ $# -ge 2 ] || { usage >&2; exit 2; }
      RESOLVE_ADDR=$2
      shift
      ;;
    --base)
      [ $# -ge 2 ] || { usage >&2; exit 2; }
      BASE=$2
      shift
      ;;
    *)
      printf 'verify.sh: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ -n "$RESOLVE_ADDR" ] && [ "$BASE" != "https://$REAL_WWW" ]; then
  printf 'verify.sh: --resolve and --base are mutually exclusive\n' >&2
  exit 2
fi
if [ -n "$RESOLVE_ADDR" ]; then
  MODE=resolve
elif [ "$BASE" = "https://$REAL_WWW" ]; then
  MODE=public
else
  MODE=base
fi

# In the pre-DNS run the certificate is not issued yet (Pages provisions it
# only once DNS points at it), so the content is verified but not the chain;
# check 8 reports the presented certificate for the eye instead.
CURLX=
if [ "$MODE" = resolve ]; then
  CURLX="-k --resolve $REAL_WWW:443:$RESOLVE_ADDR"
fi

BASE_HOST=${BASE#*://}
BASE_HOST=${BASE_HOST%%/*}
BASE_HOST=${BASE_HOST%%:*}

# Checks 6-8 are about the public names (apex 301, http->https, the
# certificate), so they are judged only when this run is aimed at those names.
NAME_CHECKS=no
if [ "$MODE" = public ]; then
  NAME_CHECKS=yes
elif [ "$MODE" = base ] && { [ "$BASE_HOST" = "$REAL_WWW" ] || [ "$BASE_HOST" = "$REAL_APEX" ]; }; then
  NAME_CHECKS=yes
fi
NAME_SKIP_REASON=
if [ "$NAME_CHECKS" = no ]; then
  if [ "$MODE" = resolve ]; then
    NAME_SKIP_REASON="pre-DNS: the public names still point at the old host"
  else
    NAME_SKIP_REASON="the base is not the public name"
  fi
fi

TAB=$(printf '\t')
WFMT="%{http_code}${TAB}%{content_type}${TAB}%{size_download}${TAB}%{redirect_url}"

# fetch URL — sets CODE, CT, SIZE, RURL; ERR is set when the transport fails.
fetch() {
  CODE= CT= SIZE= RURL= ERR=
  res=$(curl -sS $CURLX -o /dev/null -w "$WFMT" "$1" 2>&1)
  rc=$?
  CODE=$(printf '%s\n' "$res" | tail -n 1 | cut -d"$TAB" -f1)
  CT=$(printf '%s\n' "$res" | tail -n 1 | cut -d"$TAB" -f2)
  SIZE=$(printf '%s\n' "$res" | tail -n 1 | cut -d"$TAB" -f3)
  RURL=$(printf '%s\n' "$res" | tail -n 1 | cut -d"$TAB" -f4)
  if [ $rc -ne 0 ]; then
    ERR=$(printf '%s\n' "$res" | sed '$d' | tr '\n' ' ')
  fi
}

# asset_desc — one-line reason the last fetch did not do what was wanted.
asset_desc() {
  if [ -n "$ERR" ]; then
    printf '%s' "$ERR"
  else
    printf '%s %s' "$CODE" "${CT:-no type}"
  fi
}

ct_ok() {
  case $CT in
    "$1"*) return 0 ;;
  esac
  return 1
}

case $MODE in
  resolve)
    printf 'verifying https://%s forced at %s (pre-DNS run: 6-7 skipped, 8 for the eye)\n' \
      "$REAL_WWW" "$RESOLVE_ADDR"
    ;;
  base)
    if [ "$NAME_CHECKS" = yes ]; then
      printf 'verifying %s (base is the public name: 6-8 judged)\n' "$BASE"
    else
      printf 'verifying %s (6-8 skipped: the base is not the public name)\n' "$BASE"
    fi
    ;;
  *)
    printf 'verifying %s (public run: all checks judged)\n' "$BASE"
    ;;
esac

# 1. Every page is 200
bad=
for p in index about schedule results postal howto host highstart; do
  fetch "$BASE/$p.html"
  if [ -n "$ERR" ] || [ "$CODE" != 200 ]; then
    bad="$bad $p.html($(asset_desc))"
  fi
done
if [ -z "$bad" ]; then
  ok "1   all 8 pages 200"
else
  fail "1   pages not 200:$bad"
fi

# 2. The stylesheet and a representative asset
bad=
fetch "$BASE/styles.css"
if [ -n "$ERR" ] || [ "$CODE" != 200 ] || ! ct_ok text/css; then
  bad="$bad styles.css($(asset_desc))"
fi
fetch "$BASE/assets/wagon.jpg"
if [ -n "$ERR" ] || [ "$CODE" != 200 ] || ! ct_ok image/jpeg; then
  bad="$bad assets/wagon.jpg($(asset_desc))"
fi
fetch "$BASE/assets/PhxPilots.JPG"
if [ -n "$ERR" ] || [ "$CODE" != 200 ] || ! ct_ok image/jpeg; then
  bad="$bad assets/PhxPilots.JPG($(asset_desc))"
fi
if [ -z "$bad" ]; then
  ok "2   styles.css text/css, assets/wagon.jpg image/jpeg, assets/PhxPilots.JPG image/jpeg"
else
  fail "2   stylesheet/assets wrong:$bad (want 200 + text/css, image/jpeg, image/jpeg)"
fi

# 3. R8 — the download, with spaces in its name, must come down as application/msword
fetch "$BASE/$DOCS"
if [ -z "$ERR" ] && [ "$CODE" = 200 ] && ct_ok application/msword && [ "$SIZE" = "$DOCS_SIZE" ]; then
  ok "3   bulletin 200 application/msword $DOCS_SIZE bytes"
else
  fail "3   bulletin $(asset_desc) (want 200 application/msword $DOCS_SIZE bytes)"
fi

# 4. R9 — a missing path is a 404, not a 403 and not a redirect to the home page
fetch "$BASE/no-such-page.html"
if [ -z "$ERR" ] && [ "$CODE" = 404 ]; then
  ok "4   missing path is a 404"
else
  fail "4   missing path $(asset_desc) (want 404)"
fi

# 5. R9 — no directory listing
fetch "$BASE/assets/"
if [ -z "$ERR" ] && [ "$CODE" != 200 ]; then
  ok "5   assets/ has no directory listing ($CODE)"
else
  fail "5   assets/ $(asset_desc) (want 403 or 404, never a 200 listing)"
fi

# 6. R3 — bare domain 301s to www, over HTTPS
if [ "$NAME_CHECKS" = yes ]; then
  fetch "https://$REAL_APEX/"
  if [ -z "$ERR" ] && [ "$CODE" = 301 ] && [ "$RURL" = "https://$REAL_WWW/" ]; then
    ok "6   apex 301 -> https://$REAL_WWW/"
  else
    fail "6   apex $(asset_desc) (want 301 -> https://$REAL_WWW/)"
  fi
else
  skip "6   apex -> www 301  ($NAME_SKIP_REASON)"
fi

# 7. HTTP redirects to HTTPS
if [ "$NAME_CHECKS" = yes ]; then
  fetch "http://$REAL_WWW/"
  case $CODE in
    301|302|307|308) redir=yes ;;
    *) redir=no ;;
  esac
  if [ -z "$ERR" ] && [ "$redir" = yes ] && [ "${RURL#https://$REAL_WWW/}" != "$RURL" ]; then
    ok "7   http -> https ($CODE -> $RURL)"
  else
    fail "7   http://$REAL_WWW/ $(asset_desc) (want a redirect to https://$REAL_WWW/)"
  fi
else
  skip "7   http -> https  ($NAME_SKIP_REASON)"
fi

# 8. R2 — the certificate covers both names and is not the old *.bizland.com one
case $MODE in
  resolve) CERT_HOST=$RESOLVE_ADDR ;;
  *) CERT_HOST=$REAL_WWW ;;
esac
cert=$(
  printf '' | openssl s_client -connect "$CERT_HOST:443" -servername "$REAL_WWW" 2>/dev/null \
    | openssl x509 -noout -subject -issuer -ext subjectAltName 2>/dev/null
)
cert_oneline=$(printf '%s' "$cert" | tr '\n' ' ')
if [ "$MODE" = resolve ]; then
  info "8   certificate presented at $CERT_HOST (for the eye, not judged): $cert_oneline"
else
  san_www=no
  san_apex=no
  rapid=no
  if [ -n "$cert" ]; then
    printf '%s\n' "$cert" | grep -q "DNS:$REAL_WWW" && san_www=yes
    printf '%s\n' "$cert" | grep -q "DNS:$REAL_APEX" && san_apex=yes
    issuer=$(printf '%s\n' "$cert" | grep '^issuer=' | head -n 1)
    [ -n "$issuer" ] && printf '%s' "$issuer" | grep -qi 'rapidssl' && rapid=yes
  fi
  if [ -z "$cert" ]; then
    fail "8   no certificate presented on $CERT_HOST:443"
  elif [ "$san_www" = yes ] && [ "$san_apex" = yes ] && [ "$rapid" = no ]; then
    ok "8   certificate covers both names ($issuer)"
  else
    fail "8   certificate wrong (SAN www=$san_www apex=$san_apex rapidssl=$rapid): $cert_oneline"
  fi
fi

# 9. R10 — mail untouched: run before AND after the cutover, diff the output
if command -v dig >/dev/null 2>&1; then
  mx=$(dig +short @8.8.8.8 "$REAL_APEX" MX 2>/dev/null | tr '\n' ' ')
  txt=$(dig +short @8.8.8.8 "$REAL_APEX" TXT 2>/dev/null | tr '\n' ' ')
  info "9   mail records (diff before/after): MX ${mx:-none} | TXT ${txt:-none}"
else
  skip "9   mail records  (dig not installed)"
fi

# 10. R11 — a plain client is served; no user-agent games
plain=$(curl -sS $CURLX --user-agent '' -o /dev/null -w '%{http_code}' "$BASE/" 2>&1)
prc=$?
plain_code=$(printf '%s\n' "$plain" | tail -n 1)
plain_err=
[ $prc -ne 0 ] && plain_err=$(printf '%s\n' "$plain" | sed '$d' | tr '\n' ' ')
custom=$(curl -sS $CURLX --user-agent 'curl-check/1.0' -o /dev/null -w '%{http_code}' "$BASE/" 2>&1)
crc=$?
custom_code=$(printf '%s\n' "$custom" | tail -n 1)
custom_err=
[ $crc -ne 0 ] && custom_err=$(printf '%s\n' "$custom" | sed '$d' | tr '\n' ' ')
if [ -z "$plain_err" ] && [ -z "$custom_err" ] && [ "$plain_code" = 200 ] && [ "$custom_code" = 200 ]; then
  ok "10  plain and custom user agents both 200"
else
  fail "10  user agents: plain=${plain_err:-$plain_code} custom=${custom_err:-$custom_code} (want 200 200)"
fi

# 11. F3L only — the two F3XVault iframes must not be blocked by a new header
hdrs=$(curl -sS $CURLX -o /dev/null -D - "$BASE/results.html" 2>/dev/null | tr -d '\r')
xfo=$(printf '%s\n' "$hdrs" | grep -i '^x-frame-options:' | head -n 1)
csp=$(printf '%s\n' "$hdrs" | grep -i '^content-security-policy:' | head -n 1)
if [ -n "$xfo" ]; then
  fail "11  $xfo would block the F3XVault iframes"
elif [ -n "$csp" ] && ! printf '%s' "$csp" | grep -qi 'f3xvault'; then
  fail "11  $csp does not allow the F3XVault iframes"
else
  ok "11  no CSP or X-Frame-Options blocks the F3XVault iframes"
fi

# 12. Case sensitivity is unchanged
fetch "$BASE/Index.html"
if [ -z "$ERR" ] && [ "$CODE" = 404 ]; then
  ok "12  Index.html is a 404 (case sensitivity intact)"
else
  fail "12  Index.html $(asset_desc) (want 404)"
fi

# 13. (added, not in §11) the publish tree exposes none of the repo's
# non-site content; one representative step folder is probed
bad=
for probe in decisions/ deploy/ README.txt step-0-design-and-implement-an-ftp-deployment/; do
  fetch "$BASE/$probe"
  if [ -n "$ERR" ] || [ "$CODE" != 404 ]; then
    bad="$bad $probe($(asset_desc))"
  fi
done
if [ -z "$bad" ]; then
  ok "13  decisions/, deploy/, README.txt and a step folder are all 404"
else
  fail "13  reachable where they must be 404:$bad"
fi

# robots.txt — reported, not judged: 404 is correct on Pages, and the old
# host serves an empty one, which means the same thing to crawlers.
fetch "$BASE/robots.txt"
if [ -n "$ERR" ]; then
  info "    robots.txt transport error: $ERR"
else
  info "    robots.txt $CODE (404 is correct on Pages; 200+empty is what the old host does)"
fi

printf '\n%d checks: %d ok, %d failed, %d skipped\n' "$((n_ok + n_fail + n_skip))" \
  "$n_ok" "$n_fail" "$n_skip"
[ "$n_fail" -gt 0 ] && exit 1
exit 0
