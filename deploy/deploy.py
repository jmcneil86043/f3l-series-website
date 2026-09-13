#!/usr/bin/env python3
"""Publish the F3L Contest Series site over FTP, uploading only what changed.

Dry run is the default: the script connects, compares the local deploy set with
the manifest it keeps on the server, prints the plan and sends nothing. Pass
--upload to perform the plan. See deploy/README.md for setup and usage.

Python 3.9+, standard library only.
"""

import argparse
import getpass
import hashlib
import io
import json
import os
import socket
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from ftplib import FTP, all_errors, error_perm
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent

# What gets published: every top-level *.html, styles.css, and everything under
# assets/. Anything whose name starts with "." is never part of the site.
DEPLOY_STYLESHEET = "styles.css"
DEPLOY_DIR = "assets"

MANIFEST_NAME = ".f3l-deploy-manifest.json"
MANIFEST_VERSION = 1
UPLOAD_SUFFIX = ".uploading"

DEFAULTS = {
    "F3L_FTP_HOST": "ftp.mcneilco.com",
    "F3L_FTP_USER": "jmcneil",
    "F3L_FTP_REMOTE_DIR": "/f3l_series",
}
PASSWORD_KEY = "F3L_FTP_PASSWORD"
OP_REF_KEY = "F3L_FTP_PASSWORD_OP_REF"
ENV_FILE_KEY = "F3L_DEPLOY_ENV"
DEFAULT_ENV_FILE = Path("~/.config/f3l-series-website/deploy.env")

FTP_TIMEOUT = 60

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


class UsageError(Exception):
    """A problem the user fixes with configuration or flags (exit 2)."""


# --- Deploy set --------------------------------------------------------------

def is_deploy_path(rel):
    """True if the repo-relative POSIX path belongs to the published site."""
    parts = PurePosixPath(rel).parts
    if not parts or any(p.startswith(".") for p in parts):
        return False
    if len(parts) == 1:
        return parts[0] == DEPLOY_STYLESHEET or parts[0].lower().endswith(".html")
    return parts[0] == DEPLOY_DIR


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_deploy_set(root):
    """Map each deploy-set path (POSIX, relative to root) to {"sha256", "size"}."""
    root = Path(root)
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            if is_deploy_path(rel) and full.is_file():
                files[rel] = {"sha256": sha256_file(full), "size": full.stat().st_size}
    return dict(sorted(files.items()))


# --- Plan --------------------------------------------------------------------

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


def is_managed_remote_path(rel):
    """Remote files the deploy may report or delete: not the manifest, no dotfiles."""
    return not any(p.startswith(".") for p in PurePosixPath(rel).parts)


def compute_plan(local, manifest, listing, force=False):
    """Classify files. Pure: local and manifest files are path -> {sha256, size},
    listing is remote path -> size, manifest may be None."""
    recorded = manifest.get("files") if manifest else None
    if not isinstance(recorded, dict):
        recorded = None
    plan = Plan()
    for rel, info in sorted(local.items()):
        if recorded is None or rel not in recorded or rel not in listing:
            plan.new.append(rel)
        elif force or recorded[rel].get("sha256") != info["sha256"]:
            plan.changed.append(rel)
        elif listing[rel] != recorded[rel].get("size"):
            plan.changed.append(rel)
        else:
            plan.unchanged.append(rel)
    plan.remote_only = sorted(
        rel for rel in listing if rel not in local and is_managed_remote_path(rel)
    )
    return plan


def build_manifest(local, git_commit, git_dirty, deployed_by, now=None):
    now = now or datetime.now(timezone.utc)
    return {
        "version": MANIFEST_VERSION,
        "deployed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "deployed_by": deployed_by,
        "files": local,
    }


# --- Remote ------------------------------------------------------------------

class Remote:
    """What the deploy needs from the server. Paths are relative to the remote dir."""

    def read_manifest(self):
        raise NotImplementedError

    def listing(self):
        raise NotImplementedError

    def mkdir(self, rel_dir):
        raise NotImplementedError

    def upload(self, rel, local_path):
        raise NotImplementedError

    def write_manifest(self, manifest):
        raise NotImplementedError

    def delete(self, rel):
        raise NotImplementedError

    def close(self):
        pass


class FtpRemote(Remote):
    """Plain FTP, passive mode, one connection. Uploads go to <name>.uploading
    and are renamed over the target so a half-sent file never serves."""

    def __init__(self, host, user, password, remote_dir, verbose=False, timeout=FTP_TIMEOUT):
        self.ftp = FTP(timeout=timeout)
        if verbose:
            self.ftp.set_debuglevel(1)  # ftplib masks the PASS command in its log
        self.ftp.connect(host, 21)
        self.ftp.login(user, password)
        self.ftp.set_pasv(True)
        try:
            self.ftp.cwd(remote_dir)
        except error_perm as exc:
            self.close()
            raise UsageError(
                f"remote directory {remote_dir!r} does not exist on {host} ({exc}); "
                "refusing to create it — check F3L_FTP_REMOTE_DIR"
            ) from None
        self.base = self.ftp.pwd().rstrip("/")
        self._dirs = {""}

    def _abs(self, rel):
        return f"{self.base}/{rel}" if rel else self.base or "/"

    def read_manifest(self):
        buf = io.BytesIO()
        try:
            self.ftp.retrbinary(f"RETR {self._abs(MANIFEST_NAME)}", buf.write)
        except error_perm:
            return None
        try:
            manifest = json.loads(buf.getvalue().decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            print(f"warning: {MANIFEST_NAME} on the server is unreadable; treating it as absent",
                  file=sys.stderr)
            return None
        return manifest if isinstance(manifest, dict) else None

    def listing(self):
        files = {}
        pending = [""]
        while pending:
            rel_dir = pending.pop()
            self._dirs.add(rel_dir)
            for name, facts in self.ftp.mlsd(self._abs(rel_dir), facts=["type", "size"]):
                kind = facts.get("type", "").lower()
                if name in (".", "..") or kind in ("cdir", "pdir"):
                    continue
                rel = f"{rel_dir}/{name}" if rel_dir else name
                if kind == "dir":
                    pending.append(rel)
                elif kind == "file":
                    files[rel] = int(facts.get("size", -1))
        return dict(sorted(files.items()))

    def mkdir(self, rel_dir):
        if rel_dir in self._dirs:
            return
        try:
            self.ftp.mkd(self._abs(rel_dir))
        except error_perm:
            # Already there (e.g. an empty directory the listing saw no files in).
            self.ftp.cwd(self._abs(rel_dir))
            self.ftp.cwd(self.base or "/")
        self._dirs.add(rel_dir)

    def _store(self, rel, fh):
        target = self._abs(rel)
        temp = target + UPLOAD_SUFFIX
        self.ftp.storbinary(f"STOR {temp}", fh)
        try:
            self.ftp.rename(temp, target)
        except error_perm:
            # Some servers refuse to rename over an existing file.
            self.ftp.delete(target)
            self.ftp.rename(temp, target)

    def upload(self, rel, local_path):
        with open(local_path, "rb") as fh:
            self._store(rel, fh)

    def write_manifest(self, manifest):
        data = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        self._store(MANIFEST_NAME, io.BytesIO(data))

    def delete(self, rel):
        self.ftp.delete(self._abs(rel))

    def close(self):
        try:
            self.ftp.quit()
        except all_errors:
            self.ftp.close()


def parent_dirs(rel):
    """"assets/highstart/a.png" -> ["assets", "assets/highstart"]."""
    parts = PurePosixPath(rel).parts[:-1]
    return ["/".join(parts[: i + 1]) for i in range(len(parts))]


def execute_plan(plan, root, remote, manifest, delete=False, log=print):
    """Upload new and changed files, optionally delete remote-only files, then
    write the manifest. Any exception propagates before the manifest is written."""
    root = Path(root)
    for rel in plan.to_upload:
        for rel_dir in parent_dirs(rel):
            remote.mkdir(rel_dir)
        remote.upload(rel, root / rel)
        log(f"  uploaded  {rel}")
    if delete:
        for rel in plan.remote_only:
            remote.delete(rel)
            log(f"  deleted   {rel}")
    remote.write_manifest(manifest)
    log(f"  wrote     {MANIFEST_NAME}")


# --- Credentials -------------------------------------------------------------

@dataclass
class Settings:
    host: str
    user: str
    password: str = field(repr=False)
    remote_dir: str
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


def op_read(ref):
    """Resolve a 1Password reference with the op CLI; the secret comes back on stdout."""
    try:
        result = subprocess.run(["op", "read", ref], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise UsageError(f"{OP_REF_KEY} is set but the 1Password CLI (op) is not installed") from None
    if result.returncode != 0:
        raise UsageError(f"op read {ref} failed: {result.stderr.strip() or 'no output'}")
    return result.stdout.rstrip("\r\n")


def resolve_settings(environ, env_file=None, warn=None, read_op=op_read):
    """Each setting: process environment, then the env file, then (password only)
    a 1Password reference, then the non-secret defaults."""
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
        return environ.get(key) or from_file.get(key) or ""

    password = lookup(PASSWORD_KEY)
    if not password:
        ref = lookup(OP_REF_KEY)
        if ref:
            password = read_op(ref)
    if not password:
        raise UsageError(
            f"no FTP password: set {PASSWORD_KEY} (or {OP_REF_KEY}) in the environment "
            f"or in {path}"
        )
    return Settings(
        host=lookup("F3L_FTP_HOST") or DEFAULTS["F3L_FTP_HOST"],
        user=lookup("F3L_FTP_USER") or DEFAULTS["F3L_FTP_USER"],
        password=password,
        remote_dir=lookup("F3L_FTP_REMOTE_DIR") or DEFAULTS["F3L_FTP_REMOTE_DIR"],
        env_file=path,
    )


# --- Git ---------------------------------------------------------------------

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
    """(commit, dirty_deploy_paths). commit is None and dirty is None when git
    cannot answer (not a checkout, git missing)."""
    try:
        head = run(["git", "-C", str(root), "rev-parse", "HEAD"],
                   capture_output=True, text=True, check=False)
        status = run(["git", "-C", str(root), "status", "--porcelain", "-z",
                      "--untracked-files=all"],
                     capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None, None
    if head.returncode != 0 or status.returncode != 0:
        return None, None
    dirty = sorted({p for p in parse_porcelain_z(status.stdout) if is_deploy_path(p)})
    return head.stdout.strip(), dirty


# --- Report and CLI ----------------------------------------------------------

def format_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def print_plan(plan, local, delete, upload, out=print):
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
            size = f"  {format_size(local[rel]['size'])}" if rel in local else ""
            out(f"  {rel}{size}")
    upload_bytes = sum(local[rel]["size"] for rel in plan.new + plan.changed)
    out(
        f"Totals: {len(plan.new)} new, {len(plan.changed)} changed, "
        f"{len(plan.unchanged)} unchanged, {len(plan.remote_only)} remote-only; "
        f"{format_size(upload_bytes)} to send"
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="deploy.py",
        description="Publish the F3L Contest Series site over FTP. Dry run unless --upload.",
    )
    parser.add_argument("--upload", action="store_true",
                        help="perform the plan (default is a dry run that sends nothing)")
    parser.add_argument("--force", action="store_true",
                        help="treat every file as changed and rebuild the manifest")
    parser.add_argument("--delete", action="store_true",
                        help="also delete remote files that are not in the deploy set")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="permit --upload with uncommitted changes to site files")
    parser.add_argument("--env", metavar="PATH",
                        help=f"env file (default: ${ENV_FILE_KEY}, else {DEFAULT_ENV_FILE})")
    parser.add_argument("--verbose", action="store_true",
                        help="log FTP commands (the password is masked)")
    return parser


def main(argv=None, environ=None, root=None, remote_factory=None, git=git_state):
    args = build_parser().parse_args(argv)
    environ = os.environ if environ is None else environ
    root = Path(root) if root is not None else REPO_ROOT
    remote_factory = remote_factory or (
        lambda s: FtpRemote(s.host, s.user, s.password, s.remote_dir, verbose=args.verbose)
    )

    try:
        settings = resolve_settings(environ, env_file=args.env)
        local = collect_deploy_set(root)
        if not local:
            raise UsageError(f"no site files found under {root}")
        commit, dirty = git(root)
        if args.upload and dirty != [] and not args.allow_dirty:
            if dirty is None:
                detail = "git cannot report the state of the checkout"
            else:
                detail = "uncommitted changes to: " + ", ".join(dirty)
            raise UsageError(f"refusing to upload: {detail} (commit first, or pass --allow-dirty)")
    except UsageError as exc:
        print(f"deploy.py: {exc}", file=sys.stderr)
        return EXIT_USAGE

    mode = "UPLOAD" if args.upload else "DRY RUN (nothing will be sent; pass --upload to publish)"
    state = " (git state unknown)" if dirty is None else " (dirty)" if dirty else ""
    print(mode)
    print(f"Local:  {root} @ {commit or 'unknown commit'}{state}")
    print(f"Remote: ftp://{settings.user}@{settings.host}{settings.remote_dir}")

    remote = None
    try:
        remote = remote_factory(settings)
        manifest = remote.read_manifest()
        listing = remote.listing()
        if manifest is None:
            print(f"No {MANIFEST_NAME} on the server: every file counts as new.")
        else:
            print(f"Last deploy: {manifest.get('deployed_at', '?')} of "
                  f"{manifest.get('git_commit') or 'unknown commit'} by {manifest.get('deployed_by', '?')}")
        plan = compute_plan(local, manifest, listing, force=args.force)
        print_plan(plan, local, delete=args.delete, upload=args.upload)

        if not args.upload:
            return EXIT_OK
        if not plan.to_upload and not (args.delete and plan.remote_only):
            print("Nothing to do.")
            return EXIT_OK
        deployed_by = f"{getpass.getuser()}@{socket.gethostname().split('.')[0]}"
        new_manifest = build_manifest(local, commit, dirty is None or bool(dirty), deployed_by)
        print("Transfer:")
        execute_plan(plan, root, remote, new_manifest, delete=args.delete)
        print(f"Done: {len(plan.to_upload)} uploaded"
              f"{f', {len(plan.remote_only)} deleted' if args.delete else ''}; "
              f"manifest records {commit or 'unknown commit'}.")
        return EXIT_OK
    except UsageError as exc:
        print(f"deploy.py: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except all_errors as exc:
        print(f"deploy.py: FTP failure: {exc}", file=sys.stderr)
        if args.upload:
            print("The server manifest was not updated; re-run to resend what was in flight.",
                  file=sys.stderr)
        return EXIT_FAILURE
    finally:
        if remote is not None:
            remote.close()


if __name__ == "__main__":
    sys.exit(main())
