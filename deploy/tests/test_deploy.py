#!/usr/bin/env python3
"""Tests for deploy.py — the GitHub Pages publisher.

No network and no real remote: each CLI test builds a temp bare repository
that stands in for the GitHub repo (a per-repo URL rewrite makes a
GitHub-form remote URL resolve to the local bare path) plus a temp site
checkout whose origin is that rewrite. The live-site check is always injected
and by default refuses to connect. Run from the repo root:

    python3 -m unittest discover -s deploy/tests
"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import deploy  # noqa: E402  (deploy/deploy.py)

GITHUB_URL = "git@github.com:jmcneil86043/f3l-series-website.git"

FILES = {
    "index.html": b"<h1>home</h1>",
    "about.html": b"<h1>about</h1>",
    "styles.css": b"body { color: black; }",
    "assets/wagon.jpg": b"JPG-WAGON",
    "assets/highstart/image001.jpg": b"JPG-HIGH",
    "assets/F3L contest bulletin template 2026 v1.1.doc": b"DOC-TEMPLATE",
}
TOTAL_BYTES = sum(len(v) for v in FILES.values())


def run_git(cwd, args, input=None, env=None):
    res = subprocess.run(["git", "-C", str(cwd), *args],
                         capture_output=True, text=True, input=input, env=env, check=False)
    if res.returncode != 0:
        raise AssertionError(f"git {args} failed: {res.stderr}")
    return res.stdout.strip()


def git(cwd, *args):
    return run_git(cwd, list(args))


def make_site(root):
    """Write the six fixture files; returns them as {rel: bytes}."""
    for rel, data in FILES.items():
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return dict(FILES)


def make_temp_site(base):
    """(site, bare, files): a temp bare repo as the stand-in for GitHub and a
    committed site checkout whose origin is a GitHub-form URL rewritten to it."""
    base = Path(base)
    bare = base / "origin.git"
    site = base / "site"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    git(bare, "config", "user.name", "Test")
    git(bare, "config", "user.email", "test@example.com")
    subprocess.run(["git", "init", "-q", str(site)], check=True)
    git(site, "config", "user.name", "Test")
    git(site, "config", "user.email", "test@example.com")
    git(site, "remote", "add", "origin", GITHUB_URL)
    git(site, "config", f"url.{bare}.insteadOf", GITHUB_URL)
    files = make_site(site)
    git(site, "add", "-A")
    git(site, "commit", "-q", "-m", "site")
    return site, bare, files


def advance_branch_with_stray(bare, name="stray.html", content=b"stray page\n"):
    """Commit name onto the bare's gh-pages branch, as if someone else pushed."""
    tip = git(bare, "rev-parse", "refs/heads/gh-pages")
    blob = run_git(bare, ["hash-object", "-w", "--stdin"], input=content.decode())
    fd, index = tempfile.mkstemp(prefix=".f3l-test-index-")
    os.close(fd)
    env = dict(os.environ, GIT_INDEX_FILE=index)
    try:
        run_git(bare, ["read-tree", "refs/heads/gh-pages"], env=env)
        run_git(bare, ["update-index", "--add", "--cacheinfo",
                       f"100644,{blob},{name}"], env=env)
        tree = run_git(bare, ["write-tree"], env=env)
        commit = run_git(bare, ["commit-tree", tree, "-p", tip, "-m", "stray push"], env=env)
    finally:
        os.unlink(index)
    git(bare, "update-ref", "refs/heads/gh-pages", commit)
    return commit


def no_network(url):
    raise deploy.LiveFetchError("network disabled in tests")


class DeploySetTest(unittest.TestCase):
    def test_is_deploy_path(self):
        for rel in ["index.html", "PAGE.HTML", "styles.css", "assets/wagon.jpg",
                    "assets/highstart/image001.jpg",
                    "assets/F3L contest bulletin template 2026 v1.1.doc"]:
            self.assertTrue(deploy.is_deploy_path(rel), rel)
        for rel in ["README.md", "deploy/deploy.py", ".hidden", "assets/.secret/x.jpg",
                    "src/a.html", "styles.css.map", "assets", ""]:
            self.assertFalse(deploy.is_deploy_path(rel), rel)

    def test_collect_deploy_set(self):
        with tempfile.TemporaryDirectory(prefix="f3l-deployset-") as tmp:
            root = Path(tmp)
            make_site(root)
            (root / "README.md").write_text("no\n")
            (root / "deploy").mkdir()
            (root / "deploy" / "deploy.py").write_text("# no\n")
            (root / ".env").write_text("no\n")
            (root / "assets" / ".cache").mkdir()
            (root / "assets" / ".cache" / "x").write_bytes(b"no")
            sizes = deploy.collect_deploy_set(root)
        self.assertEqual(sizes, {rel: len(data) for rel, data in FILES.items()})

    def test_collect_deploy_set_empty(self):
        with tempfile.TemporaryDirectory(prefix="f3l-deployset-") as tmp:
            self.assertEqual(deploy.collect_deploy_set(tmp), {})


class EnvFileTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="f3l-env-")
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self._default = deploy.DEFAULT_ENV_FILE
        deploy.DEFAULT_ENV_FILE = self.dir / "deploy.env"  # absent unless a test writes it
        self.addCleanup(setattr, deploy, "DEFAULT_ENV_FILE", self._default)

    def write_env(self, text, name="deploy.env"):
        path = self.dir / name
        path.write_text(text)
        return path

    def test_defaults_when_nothing(self):
        s = deploy.resolve_settings({})
        self.assertEqual(s.remote, "origin")
        self.assertEqual(s.branch, "gh-pages")
        self.assertEqual(s.domain, "www.f3lcontestseries.org")
        self.assertEqual(s.site_url, "https://www.f3lcontestseries.org")
        self.assertEqual(s.env_file, self.dir / "deploy.env")

    def test_file_values_and_url_trailing_slash(self):
        self.write_env("F3L_PAGES_REMOTE=other\nF3L_SITE_URL=https://x.test/\n")
        s = deploy.resolve_settings({})
        self.assertEqual(s.remote, "other")
        self.assertEqual(s.site_url, "https://x.test")

    def test_process_env_beats_file(self):
        self.write_env("F3L_PAGES_REMOTE=other\n")
        s = deploy.resolve_settings({"F3L_PAGES_REMOTE": "envremote"})
        self.assertEqual(s.remote, "envremote")

    def test_f3l_deploy_env_points_at_file(self):
        path = self.write_env("F3L_PAGES_BRANCH=pages\n", name="custom.env")
        s = deploy.resolve_settings({deploy.ENV_FILE_KEY: str(path)})
        self.assertEqual(s.branch, "pages")
        self.assertEqual(s.env_file, path)

    def test_explicit_env_file_required(self):
        with self.assertRaises(deploy.UsageError):
            deploy.resolve_settings({}, env_file=str(self.dir / "missing.env"))

    def test_parse_env_file(self):
        values = deploy.parse_env_file(
            'A=1\nexport B=2\n# comment\n\nD="4 4"\nE=\'5\'\nF = 6\n')
        self.assertEqual(values, {"A": "1", "B": "2", "D": "4 4", "E": "5", "F": "6"})

    def test_parse_env_file_malformed(self):
        with self.assertRaises(deploy.UsageError) as ctx:
            deploy.parse_env_file("A=1\nNOEQUALS\n")
        self.assertIn("line 2", str(ctx.exception))
        with self.assertRaises(deploy.UsageError):
            deploy.parse_env_file("=x\n")

    def test_load_env_file_permission_warning(self):
        path = self.write_env("A=1\n")
        os.chmod(path, 0o644)
        warnings = []
        deploy.load_env_file(path, required=False, warn=warnings.append)
        self.assertIn("chmod 600", warnings[0])

    def test_load_env_file_missing_not_required(self):
        self.assertEqual(deploy.load_env_file(self.dir / "nope", required=False,
                                              warn=lambda m: None), {})


class PorcelainZTest(unittest.TestCase):
    def test_parse_porcelain_z(self):
        self.assertEqual(
            deploy.parse_porcelain_z(" M index.html\0R  assets/new name.jpg\0assets/old.jpg\0?? deploy/x.py\0"),
            ["index.html", "assets/new name.jpg", "assets/old.jpg", "deploy/x.py"])
        self.assertEqual(deploy.parse_porcelain_z(""), [])


class GitStateTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="f3l-gitstate-")
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name) / "site"
        self.dir.mkdir()
        git(self.dir, "init", "-q")
        git(self.dir, "config", "user.name", "Test")
        git(self.dir, "config", "user.email", "test@example.com")
        (self.dir / "index.html").write_bytes(b"<h1>home</h1>")
        (self.dir / "README.md").write_text("readme\n")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "init")

    def test_clean(self):
        commit, branch, dirty = deploy.git_state(self.dir)
        self.assertEqual(commit, git(self.dir, "rev-parse", "HEAD"))
        self.assertEqual(branch, git(self.dir, "rev-parse", "--abbrev-ref", "HEAD"))
        self.assertEqual(dirty, [])

    def test_dirty_site_file(self):
        (self.dir / "index.html").write_bytes(b"<h1>home v2</h1>")
        _commit, _branch, dirty = deploy.git_state(self.dir)
        self.assertEqual(dirty, ["index.html"])

    def test_dirty_only_counts_deploy_paths(self):
        (self.dir / "README.md").write_text("readme v2\n")
        _commit, _branch, dirty = deploy.git_state(self.dir)
        self.assertEqual(dirty, [])

    def test_untracked_site_file(self):
        (self.dir / "new.html").write_bytes(b"<p>new</p>")
        _commit, _branch, dirty = deploy.git_state(self.dir)
        self.assertEqual(dirty, ["new.html"])

    def test_not_a_checkout(self):
        with tempfile.TemporaryDirectory(prefix="f3l-gitstate-") as tmp:
            self.assertEqual(deploy.git_state(tmp), (None, None, None))


class PureTest(unittest.TestCase):
    def test_compute_plan_all_new(self):
        local = {"b.html": ("a" * 40, 1), "a.html": ("b" * 40, 2), "styles.css": ("a" * 40, 3)}
        plan = deploy.compute_plan(local, {})
        self.assertEqual(plan.new, ["a.html", "b.html", "styles.css"])
        self.assertEqual(plan.changed, [])
        self.assertEqual(plan.unchanged, [])
        self.assertEqual(plan.remote_only, [])
        self.assertEqual(plan.to_upload, ["styles.css", "a.html", "b.html"])

    def test_compute_plan_matching(self):
        local = {"a.html": ("a" * 40, 1), "styles.css": ("b" * 40, 2)}
        plan = deploy.compute_plan(local, dict(local))
        self.assertEqual(plan.unchanged, ["a.html", "styles.css"])
        self.assertEqual(plan.to_upload, [])

    def test_compute_plan_blob_diff(self):
        local = {"a.html": ("a" * 40, 1), "b.html": ("b" * 40, 2), "styles.css": ("c" * 40, 3)}
        remote = {"a.html": ("a" * 40, 1), "b.html": ("d" * 40, 2), "styles.css": ("c" * 40, 3)}
        plan = deploy.compute_plan(local, remote)
        self.assertEqual(plan.changed, ["b.html"])
        self.assertEqual(plan.unchanged, ["a.html", "styles.css"])

    def test_compute_plan_force(self):
        local = {"a.html": ("a" * 40, 1), "b.html": ("b" * 40, 2)}
        plan = deploy.compute_plan(local, dict(local), force=True)
        self.assertEqual(plan.changed, ["a.html", "b.html"])
        self.assertEqual(plan.new, [])
        # --force never turns an absent remote file into a change
        plan = deploy.compute_plan(local, {}, force=True)
        self.assertEqual(plan.new, ["a.html", "b.html"])

    def test_compute_plan_remote_only_excludes_managed_extras(self):
        local = {"a.html": ("a" * 40, 1)}
        remote = {"a.html": ("a" * 40, 1), ".nojekyll": ("e" * 40, 0),
                  "CNAME": ("e" * 40, 5), "old.html": ("f" * 40, 2)}
        plan = deploy.compute_plan(local, remote)
        self.assertEqual(plan.remote_only, ["old.html"])
        self.assertEqual(plan.unchanged, ["a.html"])

    def test_parse_ls_tree(self):
        text = (
            "100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391        0\t.nojekyll\n"
            "100644 blob 8b137891791fe96927ad78e64b0aad7bded08bdc      12\tindex.html\n"
            "160000 commit 1234567890123456789012345678901234567890\tsub\n"
        )
        self.assertEqual(deploy.parse_ls_tree(text), {
            ".nojekyll": ("e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", 0),
            "index.html": ("8b137891791fe96927ad78e64b0aad7bded08bdc", 12),
        })
        self.assertEqual(deploy.parse_ls_tree(""), {})

    def test_publish_message(self):
        now = datetime(2026, 10, 16, 18, 4, 11, tzinfo=timezone.utc)
        msg = deploy.publish_message("abc1234567890", "main", False,
                                     {"a.html": ("b" * 40, 3)}, "john@host", now=now)
        self.assertEqual(msg,
                         "Publish abc1234 from main\n"
                         "\n"
                         "Source-Commit: abc1234567890\n"
                         "Source-Dirty: false\n"
                         "Deployed-By: john@host\n"
                         "Deployed-At: 2026-10-16T18:04:11Z\n"
                         "Files: 1 (3 bytes)\n")
        self.assertIn("Source-Dirty: true\n",
                      deploy.publish_message("abc1234567890", "main", True,
                                             {"a.html": ("b" * 40, 3)}, "j@h", now=now))
        self.assertIn("Source-Dirty: unknown\n",
                      deploy.publish_message("abc1234567890", "main", None,
                                             {"a.html": ("b" * 40, 3)}, "j@h", now=now))
        msg = deploy.publish_message(None, None, None, {}, "j@h", now=now)
        self.assertTrue(msg.startswith("Publish unknown from unknown branch\n"))
        self.assertIn("Source-Commit: unknown\n", msg)
        msg = deploy.publish_message("abc1234567890", "main", False,
                                     {"a": ("b" * 40, 17509460), "c": ("b" * 40, 17509460)},
                                     "j@h", now=now)
        self.assertIn("Files: 2 (35,018,920 bytes)\n", msg)

    def test_parse_trailers(self):
        now = datetime(2026, 10, 16, 18, 4, 11, tzinfo=timezone.utc)
        msg = deploy.publish_message("abc1234567890", "main", False,
                                     {"a.html": ("b" * 40, 3)}, "john@host", now=now)
        self.assertEqual(deploy.parse_trailers(msg), {
            "Source-Commit": "abc1234567890",
            "Source-Dirty": "false",
            "Deployed-By": "john@host",
            "Deployed-At": "2026-10-16T18:04:11Z",
            "Files": "1 (3 bytes)",
        })
        self.assertEqual(deploy.parse_trailers("Merge branch 'x'\n\nBody line\n"), {})
        self.assertEqual(deploy.parse_trailers("Just a subject\n"), {})
        self.assertEqual(
            deploy.parse_trailers("Publish abc from main\n\nSome note: with colon\n\nSource-Commit: 123\n"),
            {"Source-Commit": "123"})

    def test_github_repo_from_url(self):
        want = "jmcneil86043/f3l-series-website"
        for url in [
            "git@github.com:jmcneil86043/f3l-series-website.git",
            "https://github.com/jmcneil86043/f3l-series-website.git",
            "https://github.com/jmcneil86043/f3l-series-website",
            "ssh://git@github.com/jmcneil86043/f3l-series-website.git",
        ]:
            self.assertEqual(deploy.github_repo_from_url(url), want, url)
        for url in ["git@github.com:jmcneil86043",
                    "https://example.com/jmcneil86043/f3l-series-website.git",
                    "git@github.com:notarepo"]:
            self.assertIsNone(deploy.github_repo_from_url(url), url)

    def test_blob_id(self):
        self.assertEqual(deploy.blob_id(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        res = subprocess.run(["git", "hash-object", "-w", "--stdin"],
                             input="hello", capture_output=True, text=True, check=True)
        self.assertEqual(deploy.blob_id(b"hello"), res.stdout.strip())

    def test_format_size(self):
        self.assertEqual(deploy.format_size(512), "512 B")
        self.assertEqual(deploy.format_size(2048), "2.0 KB")
        self.assertEqual(deploy.format_size(3 * 1024 * 1024), "3.0 MB")


class LiveCheckTest(unittest.TestCase):
    def local_map(self):
        return {
            "a.html": (deploy.blob_id(b"<a>"), 3),
            "assets/x.jpg": (deploy.blob_id(b"JPG"), 3),
        }

    def test_match_and_urls(self):
        local = self.local_map()
        bodies = {"https://example.com/a.html": b"<a>",
                  "https://example.com/assets/x.jpg": b"JPG"}
        urls = []

        def fetch(url):
            urls.append(url)
            return bodies[url]

        status, detail = deploy.check_live(local, "https://example.com", fetch=fetch)
        self.assertEqual((status, detail), ("match", []))
        self.assertEqual(urls, ["https://example.com/a.html", "https://example.com/assets/x.jpg"])

    def test_differs(self):
        def fetch(url):
            return b"<b>" if url.endswith("a.html") else b"JPG"
        status, detail = deploy.check_live(self.local_map(), "https://example.com", fetch=fetch)
        self.assertEqual((status, detail), ("differs", ["a.html"]))

    def test_not_checked(self):
        def fetch(url):
            raise deploy.LiveFetchError("TLS error (x)")
        status, detail = deploy.check_live(self.local_map(), "https://example.com", fetch=fetch)
        self.assertEqual((status, detail), ("not-checked", "TLS error (x)"))

    def test_never_raises(self):
        def fetch(url):
            raise RuntimeError("boom")
        status, detail = deploy.check_live(self.local_map(), "https://example.com", fetch=fetch)
        self.assertEqual((status, detail), ("not-checked", "boom"))

    def test_quotes_urls_and_strips_trailing_slash(self):
        local = {"my page.html": (deploy.blob_id(b"x"), 1)}
        urls = []

        def fetch(url):
            urls.append(url)
            return b"x"

        deploy.check_live(local, "https://e.com/", fetch=fetch)
        self.assertEqual(urls, ["https://e.com/my%20page.html"])


class CliTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="f3l-cli-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.site, self.bare, self.files = make_temp_site(self.tmp)
        self._default = deploy.DEFAULT_ENV_FILE
        deploy.DEFAULT_ENV_FILE = self.tmp / "never-created.env"
        self.addCleanup(setattr, deploy, "DEFAULT_ENV_FILE", self._default)

    def run_main(self, argv, fetch=None, git=None, environ=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = deploy.main(argv, environ=environ or {}, root=self.site,
                               git=git or deploy.git_state, fetch=fetch or no_network)
        return code, out.getvalue(), err.getvalue()

    def branch_names(self):
        return git(self.bare, "ls-tree", "-r", "--name-only",
                   "refs/heads/gh-pages").splitlines()

    def tip_trailers(self):
        return deploy.parse_trailers(
            git(self.bare, "log", "-1", "--format=%B", "refs/heads/gh-pages"))

    def test_first_dry_run(self):
        code, out, err = self.run_main([])
        self.assertEqual(code, 0, err)
        self.assertIn("DRY RUN (nothing will be sent; pass --upload to publish)", out)
        head = git(self.site, "rev-parse", "HEAD")
        self.assertIn(f"Local:  {self.site} @ {head[:7]}", out)
        self.assertIn("Remote: origin/gh-pages @ absent", out)
        self.assertIn("No gh-pages branch on origin yet: every file counts as new.", out)
        self.assertIn("New (6, would be uploaded):", out)
        self.assertIn("assets/highstart/image001.jpg", out)
        self.assertIn("assets/F3L contest bulletin template 2026 v1.1.doc", out)
        self.assertIn(f"Totals: 6 new, 0 changed, 0 unchanged, 0 remote-only; "
                      f"{deploy.format_size(TOTAL_BYTES)} to send", out)
        self.assertIn("Live: not checked: network disabled in tests", out)

    def test_dry_run_ignores_dirty(self):
        (self.site / "index.html").write_text("<h1>home edited</h1>")
        code, out, _err = self.run_main([])
        self.assertEqual(code, 0)
        self.assertIn("(dirty)", out)
        self.assertIn("DRY RUN", out)

    def test_first_upload(self):
        code, out, err = self.run_main(["--upload"])
        self.assertEqual(code, 0, err)
        self.assertIn("UPLOAD", out)
        self.assertIn("Publish:", out)
        self.assertIn("pushed    origin/gh-pages", out)
        self.assertIn("Deployments: https://github.com/jmcneil86043/f3l-series-website/deployments",
                      out)
        self.assertIn("Re-run the dry run in a minute to confirm the live site matches.", out)
        names = self.branch_names()
        self.assertEqual(sorted(names), sorted(list(FILES) + [".nojekyll", "CNAME"]))
        self.assertEqual(git(self.bare, "show", "refs/heads/gh-pages:CNAME"),
                         "www.f3lcontestseries.org")
        self.assertEqual(git(self.bare, "show", "refs/heads/gh-pages:.nojekyll"), "")
        msg = git(self.bare, "log", "-1", "--format=%B", "refs/heads/gh-pages")
        trailers = self.tip_trailers()
        self.assertEqual(trailers["Source-Commit"], git(self.site, "rev-parse", "HEAD"))
        self.assertEqual(trailers["Source-Dirty"], "false")
        self.assertIn("@", trailers["Deployed-By"])
        self.assertRegex(trailers["Deployed-At"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertIn(f"Files: 6 ({TOTAL_BYTES:,} bytes)", msg)

    def test_second_upload_nothing_to_do(self):
        self.run_main(["--upload"])
        code, out, err = self.run_main(["--upload"])
        self.assertEqual(code, 0, err)
        self.assertIn("Totals: 0 new, 0 changed, 6 unchanged, 0 remote-only", out)
        self.assertIn("Nothing to do.", out)

    def test_changed_file(self):
        self.run_main(["--upload"])
        (self.site / "about.html").write_text("<h1>about v2</h1>")
        code, out, _err = self.run_main([])
        self.assertEqual(code, 0)
        self.assertIn("Changed (1, would be uploaded):", out)
        self.assertIn("  about.html", out)
        self.assertIn("Totals: 0 new, 1 changed, 5 unchanged, 0 remote-only", out)

    def test_force_publishes_new_commit_with_identical_tree(self):
        self.run_main(["--upload"])
        old = git(self.bare, "rev-parse", "refs/heads/gh-pages")
        code, out, err = self.run_main(["--upload", "--force"])
        self.assertEqual(code, 0, err)
        self.assertIn("Publish:", out)
        new = git(self.bare, "rev-parse", "refs/heads/gh-pages")
        self.assertNotEqual(old, new)
        self.assertEqual(git(self.bare, "rev-parse", f"{old}^{{tree}}"),
                         git(self.bare, "rev-parse", f"{new}^{{tree}}"))

    def test_remote_only_and_delete(self):
        self.run_main(["--upload"])
        advance_branch_with_stray(self.bare, "stray.html")
        code, out, _err = self.run_main([])
        self.assertEqual(code, 0)
        self.assertIn("Remote-only (1, left alone; --delete removes them):", out)
        self.assertIn("  stray.html", out)
        self.assertIn("Totals: 0 new, 0 changed, 6 unchanged, 1 remote-only", out)
        code, out, err = self.run_main(["--upload"])
        self.assertEqual(code, 0, err)
        self.assertIn("Nothing to do.", out)
        self.assertIn("stray.html", self.branch_names())
        code, out, err = self.run_main(["--upload", "--delete"])
        self.assertEqual(code, 0, err)
        self.assertIn("Publish:", out)
        names = self.branch_names()
        self.assertNotIn("stray.html", names)
        self.assertEqual(len(names), 8)

    def test_dirty_tree_refuses_upload(self):
        (self.site / "index.html").write_text("<h1>home edited</h1>")
        code, _out, err = self.run_main(["--upload"])
        self.assertEqual(code, 2)
        self.assertIn("refusing to upload", err)
        self.assertIn("index.html", err)
        self.assertIn("--allow-dirty", err)

    def test_allow_dirty_publishes_with_trailer(self):
        (self.site / "index.html").write_text("<h1>home edited</h1>")
        code, _out, err = self.run_main(["--upload", "--allow-dirty"])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.tip_trailers()["Source-Dirty"], "true")

    def test_unknown_git_state_refuses_upload(self):
        unknown = lambda root: (None, None, None)
        code, _out, err = self.run_main(["--upload"], git=unknown)
        self.assertEqual(code, 2)
        self.assertIn("git cannot report the state", err)
        code, out, _err = self.run_main([], git=unknown)
        self.assertEqual(code, 0)
        self.assertIn("unknown commit", out)
        self.assertIn("(git state unknown)", out)

    def test_unreachable_remote(self):
        # Stored URL stays GitHub-form (so the remote check passes) while a
        # rewrite points the transport at a path that does not exist.
        dead = "git@github.com:f3l-test/unreachable.git"
        git(self.site, "remote", "set-url", "origin", dead)
        git(self.site, "config", "url./nonexistent/f3l.git.insteadOf", dead)
        code, _out, err = self.run_main([])
        self.assertEqual(code, 1)
        self.assertIn("cannot reach origin", err)

    def test_live_check_never_changes_exit_code(self):
        def boom(url):
            raise deploy.LiveFetchError("TLS error (certificate verify failed)")
        code, out, err = self.run_main(["--upload"], fetch=boom)
        self.assertEqual(code, 0, err)
        self.assertIn("Publish:", out)
        self.assertIn("Live: not checked: TLS error (certificate verify failed)", out)

    def test_settings_reach_the_remote(self):
        upstream_url = "git@github.com:jmcneil86043/upstream-f3l.git"
        git(self.site, "remote", "add", "upstream", upstream_url)
        git(self.site, "config", f"url.{self.bare}.insteadOf", upstream_url)
        code, out, _err = self.run_main([], environ={"F3L_PAGES_REMOTE": "upstream"})
        self.assertEqual(code, 0)
        self.assertIn("Remote: upstream/gh-pages @ absent", out)
        env_file = self.tmp / "upstream.env"
        env_file.write_text("F3L_PAGES_REMOTE=upstream\n")
        code, out, _err = self.run_main(["--env", str(env_file)])
        self.assertEqual(code, 0)
        self.assertIn("Remote: upstream/gh-pages @ absent", out)


class PlumbingTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="f3l-plumbing-")
        self.addCleanup(tmp.cleanup)
        self.site, self.bare, self.files = make_temp_site(Path(tmp.name))

    def local_map(self):
        sizes = deploy.collect_deploy_set(self.site)
        blobs = deploy.local_blobs(self.site, sorted(sizes))
        return {rel: (blobs[rel], sizes[rel]) for rel in sizes}

    def tree_names(self, tree):
        return {line.split("\t", 1)[1]
                for line in git(self.site, "ls-tree", "-r", tree).splitlines()}

    def test_build_publish_tree_first_publish(self):
        local = self.local_map()
        tree = deploy.build_publish_tree(self.site, None, local, "www.example.test")
        entries = git(self.site, "ls-tree", "-r", tree).splitlines()
        self.assertEqual(len(entries), 8)
        byname = {line.split("\t", 1)[1]: line.split("\t", 1)[0].split()[2]
                  for line in entries}
        self.assertEqual(set(byname), set(FILES) | {".nojekyll", "CNAME"})
        self.assertEqual(git(self.site, "cat-file", "blob", byname["CNAME"]), "www.example.test")
        self.assertEqual(git(self.site, "cat-file", "blob", byname[".nojekyll"]), "")

    def test_build_publish_tree_keeps_and_deletes_remote_only(self):
        local = self.local_map()
        tree1 = deploy.build_publish_tree(self.site, None, local, "d.test")
        deploy.publish(self.site, "origin", "gh-pages", None, tree1, local,
                       git(self.site, "rev-parse", "HEAD"), "main", [], "t@h")
        advance_branch_with_stray(self.bare, "stray.html")
        git(self.site, "fetch", "origin", "gh-pages")  # as main() does: fetch before building
        tip2 = git(self.bare, "rev-parse", "refs/heads/gh-pages")
        keep = deploy.build_publish_tree(self.site, tip2, local, "d.test",
                                         remote_only=["stray.html"], delete=False)
        names = self.tree_names(keep)
        self.assertIn("stray.html", names)
        self.assertEqual(len(names), 9)
        dele = deploy.build_publish_tree(self.site, tip2, local, "d.test",
                                         remote_only=["stray.html"], delete=True)
        names = self.tree_names(dele)
        self.assertNotIn("stray.html", names)
        self.assertEqual(len(names), 8)
        self.assertIn(".nojekyll", names)

    def test_publish_non_fast_forward(self):
        local = self.local_map()
        head = git(self.site, "rev-parse", "HEAD")
        branch = git(self.site, "rev-parse", "--abbrev-ref", "HEAD")
        tree = deploy.build_publish_tree(self.site, None, local, "d.test")
        first = deploy.publish(self.site, "origin", "gh-pages", None, tree, local,
                               head, branch, [], "t@h")
        stray = advance_branch_with_stray(self.bare, "stray.html")
        with self.assertRaises(deploy.GitError) as ctx:
            deploy.publish(self.site, "origin", "gh-pages", first, tree, local,
                           head, branch, [], "t@h")
        self.assertIn("push to origin/gh-pages failed", str(ctx.exception))
        self.assertIn("re-run", str(ctx.exception))
        self.assertEqual(git(self.bare, "rev-parse", "refs/heads/gh-pages"), stray)


if __name__ == "__main__":
    unittest.main()
