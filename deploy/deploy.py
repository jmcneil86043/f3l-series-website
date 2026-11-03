#!/usr/bin/env python3
"""Publish the F3L Contest Series site to GitHub Pages, pushing only what changed.

The publish tree is built from the deploy set (is_deploy_path) with git plumbing
and committed to the gh-pages branch. The change oracle is the git blob id,
compared against the tip of gh-pages, so a dry run is an exact preview of the
push; the live site is additionally fetched over HTTPS so "what is live" is
measured, not assumed. Pass --upload to perform the plan. See deploy/README.md
for setup and usage.

Python 3.9+, standard library only.
"""

import argparse
import getpass
import hashlib
import os
import re
import socket
import stat
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent

# What gets published: every top-level *.html, styles.css, and everything under
# assets/. Anything whose name starts with "." is never part of the site.
DEPLOY_STYLESHEET = "styles.css"
DEPLOY_DIR = "assets"

# Written into the publish tree on every push, so a push can never drop the
# custom domain or let Jekyll swallow underscore paths.
NOJEKYLL_NAME = ".nojekyll"
CNAME_NAME = "CNAME"

LIVE_TIMEOUT = 20
LIVE_USER_AGENT = "f3l-deploy/2"

DEFAULTS = {
    "F3L_PAGES_REMOTE": "origin",
    "F3L_PAGES_BRANCH": "gh-pages",
    "F3L_SITE_DOMAIN": "www.f3lcontestseries.org",
    "F3L_SITE_URL": "https://www.f3lcontestseries.org",
}
ENV_FILE_KEY = "F3L_DEPLOY_ENV"
DEFAULT_ENV_FILE = Path("~/.config/f3l-series-website/deploy.env")

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


class UsageError(Exception):
    """A problem the user fixes with configuration or flags (exit 2)."""


class GitError(Exception):
    """A git fetch/ls-remote/push (or other plumbing) failure (exit 1)."""


class LiveFetchError(Exception):
    """The live site could not be fetched; the live check reports not-checked."""


# --- Deploy set --------------------------------------------------------------

def is_deploy_path(rel):
    """True if the repo-relative POSIX path belongs to the published site."""
    parts = PurePosixPath(rel).parts
    if not parts or any(p.startswith(".") for p in parts):
        return False
    if len(parts) == 1:
        return parts[0] == DEPLOY_STYLESHEET or parts[0].lower().endswith(".html")
    return parts[0] == DEPLOY_DIR


def collect_deploy_set(root):
    """Map each deploy-set path (POSIX, relative to root) to its size in bytes."""
    root = Path(root)
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            if is_deploy_path(rel) and full.is_file():
                files[rel] = full.stat().st_size
    return dict(sorted(files.items()))


# --- Git plumbing ------------------------------------------------------------

def run_git(root, args, env=None, input=None, log=None):
    """Run a git command in root; log the command line when asked."""
    if log is not None:
        log(f"$ git {' '.join(args)}")
    return subprocess.run(
        ["git", "-C", str(root), *args],
        env=env, input=input, text=True, capture_output=True, check=False,
    )


def _check(res, what):
    if res.returncode != 0:
        raise GitError(f"git {what} failed: {res.stderr.strip() or 'no output'}")
    return res.stdout.strip()


def blob_id(data):
    """The git blob object id (hex) of these bytes — what hash-object computes."""
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def local_blobs(root, rels, write=False, log=None):
    """{path: git blob id} for the deploy-set paths, in one hash-object call.
    With write=True the objects are stored in the repository, which
    update-index --index-info needs."""
    args = ["hash-object", "--stdin-paths"]
    if write:
        args.append("-w")
    res = run_git(root, args, input="".join(rel + "\n" for rel in rels), log=log)
    if res.returncode != 0:
        raise GitError(f"git hash-object failed: {res.stderr.strip() or 'no output'}")
    blobs = res.stdout.split()
    if len(blobs) != len(rels):
        raise GitError(f"git hash-object returned {len(blobs)} ids for {len(rels)} paths")
    return dict(zip(rels, blobs))


def parse_ls_tree(output):
    """`git ls-tree -r -l <ref>` output -> {path: (blob, size)}; non-blob
    entries (submodules) are skipped."""
    tree = {}
    for line in output.splitlines():
        if not line:
            continue
        meta, path = line.split("\t", 1)
        parts = meta.split()
        if len(parts) == 4 and parts[1] == "blob":
            tree[path] = (parts[2], int(parts[3]))
    return tree


def fetch_remote_tree(root, remote, branch, log=None):
    """(tip, {path: (blob, size)}, tip commit message). tip is None when the
    branch does not exist on the remote; GitError when it cannot be reached."""
    res = run_git(root, ["ls-remote", remote, f"refs/heads/{branch}"], log=log)
    if res.returncode != 0:
        raise GitError(f"cannot reach {remote}: {res.stderr.strip() or 'ls-remote failed'}")
    if not res.stdout.strip():
        return None, {}, None
    res = run_git(root, ["fetch", remote, branch], log=log)
    if res.returncode != 0:
        raise GitError(f"cannot fetch {remote}/{branch}: {res.stderr.strip() or 'fetch failed'}")
    tip = _check(run_git(root, ["rev-parse", "FETCH_HEAD"], log=log), "rev-parse FETCH_HEAD")
    tree = parse_ls_tree(
        _check(run_git(root, ["ls-tree", "-r", "-l", tip], log=log), "ls-tree"))
    message = run_git(root, ["log", "-1", "--format=%B", tip]).stdout
    return tip, tree, message


def write_blob(root, text, log=None):
    """Store these bytes as a blob and return its id (a no-op if it exists)."""
    return _check(
        run_git(root, ["hash-object", "-w", "--stdin"], input=text, log=log),
        "hash-object --stdin")


def build_publish_tree(root, tip, local, domain, remote_only=None, delete=False, log=None):
    """Assemble the publish tree in a temporary index and return its object id.
    local is {path: (blob, size)}; tip is the commit to base the tree on, or
    None for the first publish. Remote-only paths survive unless delete is set.
    .nojekyll and CNAME are always written."""
    fd, index_path = tempfile.mkstemp(prefix=".f3l-deploy-index-")
    os.close(fd)
    env = dict(os.environ, GIT_INDEX_FILE=index_path)
    try:
        if tip:
            _check(run_git(root, ["read-tree", tip], env=env, log=log), "read-tree")
        else:
            _check(run_git(root, ["read-tree", "--empty"], env=env, log=log), "read-tree")
        nojekyll = write_blob(root, "", log=log)
        cname = write_blob(root, domain + "\n", log=log)
        lines = [f"100644 blob {blob}\t{rel}" for rel, (blob, _size) in sorted(local.items())]
        lines.append(f"100644 blob {nojekyll}\t{NOJEKYLL_NAME}")
        lines.append(f"100644 blob {cname}\t{CNAME_NAME}")
        res = run_git(root, ["update-index", "--index-info"],
                      env=env, input="".join(line + "\n" for line in lines), log=log)
        _check(res, "update-index --index-info")
        if delete:
            for rel in sorted(remote_only or []):
                _check(run_git(root, ["update-index", "--force-remove", rel],
                               env=env, log=log), f"update-index --force-remove {rel}")
        return _check(run_git(root, ["write-tree"], env=env, log=log), "write-tree")
    finally:
        Path(index_path).unlink(missing_ok=True)


def publish_message(commit, source_branch, dirty, local, deployed_by, now=None):
    """The commit message for a publish; the trailer block is the audit record
    that replaces the old server manifest."""
    now = now or datetime.now(timezone.utc)
    short = (commit or "unknown")[:7]
    dirty_str = "unknown" if dirty is None else ("true" if dirty else "false")
    total = sum(size for _blob, size in local.values())
    lines = [
        f"Publish {short} from {source_branch or 'unknown branch'}",
        "",
        f"Source-Commit: {commit or 'unknown'}",
        f"Source-Dirty: {dirty_str}",
        f"Deployed-By: {deployed_by}",
        f"Deployed-At: {now.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"Files: {len(local)} ({total:,} bytes)",
    ]
    return "\n".join(lines) + "\n"


def parse_trailers(message):
    """Trailer lines (Key: value) at the end of a commit message -> {key: value}."""
    trailers = {}
    for line in reversed(message.strip().splitlines()):
        if not line.strip():
            break
        key, sep, value = line.partition(":")
        if not sep or not key or " " in key:
            break
        trailers[key] = value.strip()
    return trailers


def publish(root, remote, branch, tip, tree, local, commit, source_branch, dirty,
            deployed_by, now=None, log=None):
    """Commit the publish tree on top of tip (or as the branch root) and push
    it to remote/branch; returns the new commit id. GitError if the push is
    rejected — nothing on the branch changed."""
    message = publish_message(commit, source_branch, dirty, local, deployed_by, now=now)
    args = ["commit-tree", tree]
    if tip:
        args += ["-p", tip]
    args += ["-m", message]
    new_tip = _check(run_git(root, args, log=log), "commit-tree")
    res = run_git(root, ["push", remote, f"{new_tip}:refs/heads/{branch}"], log=log)
    if res.returncode != 0:
        detail = res.stderr.strip()
        if "non-fast-forward" in detail or "rejected" in detail:
            detail += " — someone else published in between; fetch and re-run"
        raise GitError(f"push to {remote}/{branch} failed: {detail}")
    return new_tip


def github_repo_from_url(url):
    """'owner/repo' from a GitHub remote URL (ssh, ssh:// or https form), else None."""
    url = url.strip()
    if url.endswith(".git"):
        url = url[:-len(".git")]
    match = (
        re.match(r"^git@github\.com:(.+)$", url)
        or re.match(r"^https?://github\.com/(.+)$", url)
        or re.match(r"^ssh://git@github\.com/(.+)$", url)
    )
    if not match:
        return None
    repo = match.group(1).strip("/")
    return repo if "/" in repo else None


# --- Live check --------------------------------------------------------------

def http_get(url, timeout=LIVE_TIMEOUT):
    """Fetch a URL with the deploy's User-Agent; LiveFetchError on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": LIVE_USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except ssl.SSLError as exc:
        reason = getattr(exc, "reason", None) or exc
        raise LiveFetchError(f"TLS error ({reason})") from exc
    except urllib.error.HTTPError as exc:
        raise LiveFetchError(f"HTTP {exc.code}") from exc
    except socket.timeout:
        raise LiveFetchError(f"timeout after {timeout} s") from None
    except urllib.error.URLError as exc:
        raise LiveFetchError(f"cannot connect ({exc.reason})") from exc


def check_live(local, base_url, fetch=http_get, log=None):
    """(status, detail) for the live site: 'match' (all files equal the local
    tree), 'differs' (detail is the differing paths) or 'not-checked' (detail
    is the first fetch error). Informational only — it never raises."""
    base = base_url.rstrip("/")
    differs = []
    for rel in sorted(local):
        url = f"{base}/{urllib.parse.quote(rel, safe='/')}"
        if log is not None:
            log(f"live GET {url}")
        try:
            body = fetch(url)
        except Exception as exc:  # the live check must never break the run
            return "not-checked", str(exc)
        if blob_id(body) != local[rel][0]:
            differs.append(rel)
    if differs:
        return "differs", differs
    return "match", []


# --- Settings ----------------------------------------------------------------

@dataclass
class Settings:
    remote: str
    branch: str
    domain: str
    site_url: str
    env_file: Path


def parse_env_file(text):
    """KEY=value lines; blank lines and # comments ignored; optional "export "
    prefix and matching surrounding quotes stripped. Never executed."""
    values = {}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not key:
            raise UsageError(f"env file line {lineno}: expected KEY=value")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def load_env_file(path, required, warn):
    path = Path(path).expanduser()
    if not path.exists():
        if required:
            raise UsageError(f"env file {path} does not exist")
        return {}
    mode = path.stat().st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        warn(f"warning: {path} is readable by other users; run: chmod 600 {path}")
    return parse_env_file(path.read_text(encoding="utf-8"))


def resolve_settings(environ, env_file=None, warn=None):
    """Each setting: process environment, then the env file, then the default.
    The file is optional and holds nothing secret — the repo's push access is
    the deploy credential."""
    warn = warn or (lambda msg: print(msg, file=sys.stderr))
    if env_file is not None:
        path, required = Path(env_file), True
    elif environ.get(ENV_FILE_KEY):
        path, required = Path(environ[ENV_FILE_KEY]), True
    else:
        path, required = DEFAULT_ENV_FILE, False
    path = path.expanduser()
    from_file = load_env_file(path, required, warn)

    def lookup(key):
        return environ.get(key) or from_file.get(key) or DEFAULTS[key]

    return Settings(
        remote=lookup("F3L_PAGES_REMOTE"),
        branch=lookup("F3L_PAGES_BRANCH"),
        domain=lookup("F3L_SITE_DOMAIN"),
        site_url=lookup("F3L_SITE_URL").rstrip("/"),
        env_file=path,
    )


# --- Git state ---------------------------------------------------------------

def parse_porcelain_z(output):
    """Paths from `git status --porcelain -z` (rename sources included)."""
    paths = []
    entries = output.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if entry[0] in "RC":  # the next entry is the rename/copy source
            if i < len(entries) and entries[i]:
                paths.append(entries[i])
            i += 1
    return paths


def git_state(root, run=subprocess.run):
    """(commit, branch, dirty_deploy_paths). All None when git cannot answer
    (not a checkout, git missing)."""
    try:
        head = run(["git", "-C", str(root), "rev-parse", "HEAD"],
                   capture_output=True, text=True, check=False)
        branch = run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                     capture_output=True, text=True, check=False)
        status = run(["git", "-C", str(root), "status", "--porcelain", "-z",
                      "--untracked-files=all"],
                     capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None, None, None
    if head.returncode != 0 or status.returncode != 0:
        return None, None, None
    dirty = sorted({p for p in parse_porcelain_z(status.stdout) if is_deploy_path(p)})
    return head.stdout.strip(), (branch.stdout.strip() if branch.returncode == 0 else None), dirty


# --- Plan and report ---------------------------------------------------------

@dataclass
class Plan:
    new: list = field(default_factory=list)
    changed: list = field(default_factory=list)
    unchanged: list = field(default_factory=list)
    remote_only: list = field(default_factory=list)

    @property
    def to_upload(self):
        # Assets first, then the stylesheet, then pages, so a page never goes
        # live before the files it references.
        return sorted(self.new + self.changed, key=upload_order)


def upload_order(rel):
    if rel.startswith(DEPLOY_DIR + "/"):
        return (0, rel)
    if rel == DEPLOY_STYLESHEET:
        return (1, rel)
    return (2, rel)


def compute_plan(local, remote, force=False):
    """Classify files. Pure: local and remote are {path: (blob, size)}. A path
    in local but not remote is New; a blob difference (or --force) is Changed;
    the rest are Unchanged. Remote paths not in local, other than the managed
    extras (.nojekyll, CNAME), are Remote-only."""
    plan = Plan()
    for rel in sorted(local):
        if rel not in remote:
            plan.new.append(rel)
        elif force or remote[rel][0] != local[rel][0]:
            plan.changed.append(rel)
        else:
            plan.unchanged.append(rel)
    plan.remote_only = sorted(
        rel for rel in remote
        if rel not in local and rel not in (NOJEKYLL_NAME, CNAME_NAME)
    )
    return plan


def format_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def print_plan(plan, local, delete, upload, live=None, match_label="matches gh-pages", out=print):
    will = "" if upload else "would be "
    sections = [
        ("New", plan.new, f"{will}uploaded"),
        ("Changed", plan.changed, f"{will}uploaded"),
        ("Remote-only", plan.remote_only,
         f"{will}deleted" if delete else "left alone; --delete removes them"),
        ("Unchanged", plan.unchanged, "skipped"),
    ]
    for title, paths, note in sections:
        if not paths:
            continue
        out(f"{title} ({len(paths)}, {note}):")
        for rel in paths:
            size = f"  {format_size(local[rel][1])}" if rel in local else ""
            out(f"  {rel}{size}")
    upload_bytes = sum(local[rel][1] for rel in plan.new + plan.changed)
    out(
        f"Totals: {len(plan.new)} new, {len(plan.changed)} changed, "
        f"{len(plan.unchanged)} unchanged, {len(plan.remote_only)} remote-only; "
        f"{format_size(upload_bytes)} to send"
    )
    if live is not None:
        status, detail = live
        if status == "match":
            out(f"Live: {match_label}")
        elif status == "differs":
            out(f"Live: {len(detail)} files differ from the local tree:")
            for rel in detail:
                out(f"  {rel}")
        else:
            out(f"Live: not checked: {detail}")


# --- CLI ---------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="deploy.py",
        description="Publish the F3L Contest Series site to GitHub Pages. "
                    "Dry run unless --upload.",
    )
    parser.add_argument("--upload", action="store_true",
                        help="perform the plan (default is a dry run that pushes nothing)")
    parser.add_argument("--force", action="store_true",
                        help="publish a new commit even when nothing differs (Pages rebuilds)")
    parser.add_argument("--delete", action="store_true",
                        help="also drop gh-pages files that are not in the deploy set")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="permit --upload with uncommitted changes to site files")
    parser.add_argument("--env", metavar="PATH",
                        help=f"env file (default: ${ENV_FILE_KEY}, else {DEFAULT_ENV_FILE})")
    parser.add_argument("--verbose", action="store_true",
                        help="log every git command run and every URL fetched")
    return parser


def main(argv=None, environ=None, root=None, git=git_state, fetch=http_get):
    args = build_parser().parse_args(argv)
    environ = os.environ if environ is None else environ
    root = Path(root) if root is not None else REPO_ROOT
    log = print if args.verbose else None

    try:
        settings = resolve_settings(environ, env_file=args.env)
        sizes = collect_deploy_set(root)
        if not sizes:
            raise UsageError(f"no site files found under {root}")
        commit, source_branch, dirty = git(root)
        if args.upload and dirty != [] and not args.allow_dirty:
            if dirty is None:
                detail = "git cannot report the state of the checkout"
            else:
                detail = "uncommitted changes to: " + ", ".join(dirty)
            raise UsageError(f"refusing to upload: {detail} (commit first, or pass --allow-dirty)")
        # The stored remote URL, without transport rewrites (which `git remote
        # get-url` would apply), since that is what push will target on GitHub.
        url = run_git(root, ["config", f"remote.{settings.remote}.url"])
        if url.returncode != 0 or not url.stdout.strip():
            raise UsageError(f"no git remote named {settings.remote!r}")
        repo = github_repo_from_url(url.stdout)
        if repo is None:
            raise UsageError(
                f"remote {settings.remote!r} is not a GitHub URL ({url.stdout.strip()}); "
                "cannot publish")
    except UsageError as exc:
        print(f"deploy.py: {exc}", file=sys.stderr)
        return EXIT_USAGE

    mode = "UPLOAD" if args.upload else "DRY RUN (nothing will be sent; pass --upload to publish)"
    state = " (git state unknown)" if dirty is None else " (dirty)" if dirty else ""
    print(mode)
    print(f"Local:  {root} @ {commit or 'unknown commit'}{state}")

    try:
        tip, remote_tree, tip_message = fetch_remote_tree(
            root, settings.remote, settings.branch, log=log)
    except GitError as exc:
        print(f"deploy.py: {exc}", file=sys.stderr)
        return EXIT_FAILURE

    print(f"Remote: {settings.remote}/{settings.branch} @ "
          f"{tip[:7] if tip else 'absent'}")
    if tip is None:
        print(f"No {settings.branch} branch on {settings.remote} yet: every file counts as new.")
    else:
        trailers = parse_trailers(tip_message or "")
        if "Deployed-At" in trailers:
            print(f"Last deploy: {trailers['Deployed-At']} of "
                  f"{(trailers.get('Source-Commit') or 'unknown commit')[:7]} by "
                  f"{trailers.get('Deployed-By', '?')}")
        else:
            print(f"Last deploy: {tip[:7]} (no deploy trailers on the tip)")

    try:
        blobs = local_blobs(root, sorted(sizes), write=args.upload, log=log)
        local = {rel: (blobs[rel], sizes[rel]) for rel in sizes}
    except GitError as exc:
        print(f"deploy.py: {exc}", file=sys.stderr)
        return EXIT_FAILURE

    plan = compute_plan(local, remote_tree, force=args.force)
    live = check_live(local, settings.site_url, fetch=fetch, log=log)
    print_plan(plan, local, delete=args.delete, upload=args.upload, live=live,
               match_label=f"matches {settings.remote}/{settings.branch}")

    if not args.upload:
        return EXIT_OK
    if not plan.to_upload and not (args.delete and plan.remote_only) and not args.force:
        print("Nothing to do.")
        return EXIT_OK

    deployed_by = f"{getpass.getuser()}@{socket.gethostname().split('.')[0]}"
    try:
        tree = build_publish_tree(root, tip, local, settings.domain,
                                  remote_only=plan.remote_only, delete=args.delete, log=log)
        new_tip = publish(root, settings.remote, settings.branch, tip, tree, local,
                          commit, source_branch, dirty, deployed_by, log=log)
    except GitError as exc:
        print(f"deploy.py: {exc}", file=sys.stderr)
        return EXIT_FAILURE

    print("Publish:")
    print(f"  committed {new_tip}"
          + (f" on top of {tip[:7]}" if tip else " (first publish)"))
    print(f"  pushed    {settings.remote}/{settings.branch}")
    print(f"Deployments: https://github.com/{repo}/deployments")
    print("Re-run the dry run in a minute to confirm the live site matches.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
