#!/usr/bin/env python3
"""Download a safety copy of the FTP account (the whole server tree by default).

Uses the same host, user and credentials as deploy.py (see deploy/README.md).
Everything under --remote-dir is mirrored into --dest. A second run into the
same --dest resumes: files already present with the same size are skipped.
Nothing is ever written to the server.

Usage:
  deploy/backup.py                       # mirror / into ../ftp-backup-<date>
  deploy/backup.py --dest PATH           # choose the local folder
  deploy/backup.py --remote-dir /f3l_series --dest PATH
  deploy/backup.py --list                # just list what would be downloaded

Python 3.9+, standard library only.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from ftplib import FTP, all_errors, error_perm
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy  # noqa: E402  (resolve_settings, UsageError, FTP_TIMEOUT, format_size)

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_NAME = "backup-log.txt"
PART_SUFFIX = ".part"
RETRIES = 3


def connect(settings, verbose=False):
    ftp = FTP(timeout=deploy.FTP_TIMEOUT)
    if verbose:
        ftp.set_debuglevel(1)
    ftp.connect(settings.host, 21)
    ftp.login(settings.user, settings.password)
    ftp.set_pasv(True)
    return ftp


def walk(ftp, remote_dir, log):
    """Yield (remote_path, size, modify) for every regular file under remote_dir.
    Directories are listed depth-first; symlinks and odd entries are logged and skipped."""
    pending = [remote_dir.rstrip("/") or "/"]
    while pending:
        rdir = pending.pop()
        try:
            entries = list(ftp.mlsd(rdir, facts=["type", "size", "modify"]))
        except error_perm as exc:
            log(f"SKIP dir  {rdir}: {exc}")
            continue
        for name, facts in sorted(entries):
            kind = facts.get("type", "").lower()
            if name in (".", "..") or kind in ("cdir", "pdir"):
                continue
            rpath = f"{rdir.rstrip('/')}/{name}"
            if kind == "dir":
                pending.append(rpath)
            elif kind == "file":
                yield rpath, int(facts.get("size", -1)), facts.get("modify")
            else:
                log(f"SKIP {kind:<8} {rpath}")


def local_path_for(dest, remote_dir, rpath):
    rel = PurePosixPath(rpath).relative_to(PurePosixPath(remote_dir.rstrip("/") or "/"))
    return dest / Path(*rel.parts)


def set_mtime(path, modify):
    if not modify:
        return
    try:
        ts = datetime.strptime(modify[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()
        os.utime(path, (ts, ts))
    except ValueError:
        pass


def download(ftp, rpath, local, size, modify):
    local.parent.mkdir(parents=True, exist_ok=True)
    part = local.with_name(local.name + PART_SUFFIX)
    with open(part, "wb") as fh:
        ftp.retrbinary(f"RETR {rpath}", fh.write)
    got = part.stat().st_size
    if size >= 0 and got != size:
        part.unlink()
        raise OSError(f"short download: expected {size} bytes, got {got}")
    part.replace(local)
    set_mtime(local, modify)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="backup.py",
        description="Mirror the FTP account into a local folder. Read-only on the server.",
    )
    parser.add_argument("--dest", metavar="PATH",
                        help="local folder to fill (default: ../ftp-backup-<today> next to the repo)")
    parser.add_argument("--remote-dir", default="/", metavar="DIR",
                        help="server directory to mirror (default: / — the whole account)")
    parser.add_argument("--list", action="store_true",
                        help="list the remote files and totals, download nothing")
    parser.add_argument("--env", metavar="PATH", help="credentials env file (same as deploy.py)")
    parser.add_argument("--verbose", action="store_true", help="log FTP commands (password masked)")
    args = parser.parse_args(argv)

    try:
        settings = deploy.resolve_settings(os.environ, env_file=args.env)
    except deploy.UsageError as exc:
        print(f"backup.py: {exc}", file=sys.stderr)
        return deploy.EXIT_USAGE

    dest = Path(args.dest) if args.dest else REPO_ROOT.parent / f"ftp-backup-{datetime.now():%Y-%m-%d}"
    dest = dest.expanduser().resolve()
    if dest.exists() and not dest.is_dir():
        print(f"backup.py: {dest} exists and is not a directory", file=sys.stderr)
        return deploy.EXIT_USAGE

    log_fh = None
    if not args.list:
        dest.mkdir(parents=True, exist_ok=True)
        log_fh = open(dest / LOG_NAME, "a", encoding="utf-8")

    def log(msg):
        print(msg)
        if log_fh:
            log_fh.write(msg + "\n")
            log_fh.flush()

    log(f"=== backup {datetime.now():%Y-%m-%d %H:%M:%S} ftp://{settings.user}@{settings.host}{args.remote_dir}"
        f" -> {dest if not args.list else '(list only)'}")

    ftp = None
    counts = {"downloaded": 0, "skipped": 0, "failed": 0, "bytes": 0}
    failures = []
    try:
        ftp = connect(settings, args.verbose)
        files = list(walk(ftp, args.remote_dir, log))
        total_bytes = sum(max(s, 0) for _, s, _ in files)
        log(f"Remote: {len(files)} files, {deploy.format_size(total_bytes)}")
        if args.list:
            for rpath, size, _ in files:
                print(f"  {deploy.format_size(max(size, 0)):>10}  {rpath}")
            return deploy.EXIT_OK

        for i, (rpath, size, modify) in enumerate(files, 1):
            local = local_path_for(dest, args.remote_dir, rpath)
            if local.is_file() and size >= 0 and local.stat().st_size == size:
                counts["skipped"] += 1
                continue
            for attempt in range(1, RETRIES + 1):
                try:
                    download(ftp, rpath, local, size, modify)
                    counts["downloaded"] += 1
                    counts["bytes"] += max(size, 0)
                    log(f"[{i}/{len(files)}] {deploy.format_size(max(size, 0)):>10}  {rpath}")
                    break
                except error_perm as exc:
                    # 550 etc.: the server refuses this file; no point retrying.
                    counts["failed"] += 1
                    failures.append((rpath, str(exc)))
                    log(f"[{i}/{len(files)}] FAILED  {rpath}: {exc}")
                    break
                except (OSError, EOFError, *all_errors) as exc:
                    log(f"[{i}/{len(files)}] retry {attempt}/{RETRIES}  {rpath}: {exc}")
                    if attempt == RETRIES:
                        counts["failed"] += 1
                        failures.append((rpath, str(exc)))
                        log(f"[{i}/{len(files)}] FAILED  {rpath}: {exc}")
                        break
                    time.sleep(2 * attempt)
                    try:
                        ftp.close()
                    except Exception:
                        pass
                    ftp = connect(settings, args.verbose)

        log(f"Done: {counts['downloaded']} downloaded ({deploy.format_size(counts['bytes'])}), "
            f"{counts['skipped']} already present, {counts['failed']} failed.")
        if failures:
            log("Failed files:")
            for rpath, why in failures:
                log(f"  {rpath}: {why}")
            return deploy.EXIT_FAILURE
        return deploy.EXIT_OK
    except all_errors as exc:
        log(f"backup.py: FTP failure: {exc}")
        return deploy.EXIT_FAILURE
    finally:
        if ftp is not None:
            try:
                ftp.quit()
            except all_errors:
                ftp.close()
        if log_fh:
            log_fh.close()


if __name__ == "__main__":
    sys.exit(main())
