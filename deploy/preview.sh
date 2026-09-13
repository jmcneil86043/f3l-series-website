#!/bin/sh
# Serve this checkout of the F3L Contest Series site on localhost.
# Usage: deploy/preview.sh [port]     (default 8080; Ctrl-C to stop)
# Reviewing from another machine: ssh -L 8080:127.0.0.1:8080 <this host>
# See deploy/README.md.
set -eu

port="${1:-8080}"
root="$(cd "$(dirname "$0")/.." && pwd)"

echo "Serving $root"
echo "Open http://127.0.0.1:$port/  (Ctrl-C to stop)"
exec python3 -m http.server --bind 127.0.0.1 --directory "$root" "$port"
