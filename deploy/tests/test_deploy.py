"""Unit tests for deploy/deploy.py. No network: the FTP session is replaced by
FakeRemote (for the deploy flow) or FakeFtp (for FtpRemote's own commands).

Run from the repo root:  python3 -m unittest discover -s deploy/tests
"""

import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from ftplib import error_perm, error_temp
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import deploy  # noqa: E402


def write(root, rel, content):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode())
    return path


def make_site(root):
    write(root, "index.html", "<h1>home</h1>")
    write(root, "about.html", "<h1>about</h1>")
    write(root, "styles.css", "body{}")
    write(root, "assets/wagon.jpg", b"\xff\xd8jpeg")
    write(root, "assets/highstart/image001.jpg", b"\xff\xd8hs")
    write(root, "assets/F3L contest bulletin template 2026 v1.1.doc", b"doc")


class FakeRemote(deploy.Remote):
    """In-memory server: files maps remote path -> bytes."""

    def __init__(self, files=None, manifest=None, fail_on=None):
        self.files = dict(files or {})
        if manifest is not None:
            self.files[deploy.MANIFEST_NAME] = json.dumps(manifest).encode()
        self.fail_on = fail_on
        self.dirs = set()
        self.log = []
        self.closed = False

    def read_manifest(self):
        data = self.files.get(deploy.MANIFEST_NAME)
        return json.loads(data) if data is not None else None

    def listing(self):
        return {rel: len(data) for rel, data in self.files.items()}

    def mkdir(self, rel_dir):
        self.dirs.add(rel_dir)
        self.log.append(("mkdir", rel_dir))

    def upload(self, rel, local_path):
        if rel == self.fail_on:
            raise error_temp("451 transfer aborted")
        self.files[rel] = Path(local_path).read_bytes()
        self.log.append(("upload", rel))

    def write_manifest(self, manifest):
        self.files[deploy.MANIFEST_NAME] = json.dumps(manifest).encode()
        self.log.append(("manifest",))

    def delete(self, rel):
        del self.files[rel]
        self.log.append(("delete", rel))

    def close(self):
        self.closed = True


def entry(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


class DeploySetTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def test_includes_pages_stylesheet_and_assets_recursively(self):
        make_site(self.root)
        self.assertEqual(
            list(deploy.collect_deploy_set(self.root)),
            [
                "about.html",
                "assets/F3L contest bulletin template 2026 v1.1.doc",
                "assets/highstart/image001.jpg",
                "assets/wagon.jpg",
                "index.html",
                "styles.css",
            ],
        )

    def test_excludes_non_site_files_and_dotfiles(self):
        make_site(self.root)
        for rel in [
            "README.txt", "smartftp.json", "deploy/deploy.py", "deploy/README.md",
            "decisions/ledger.md", "step-0/requirements/x-design.md", "step-0/page.html",
            ".claude/settings.json", ".git/config", ".DS_Store", "assets/.DS_Store",
            "assets/.hidden/secret.jpg", "other.css", "nested/page.html",
        ]:
            write(self.root, rel, "x")
        local = deploy.collect_deploy_set(self.root)
        self.assertEqual(len(local), 6)
        self.assertNotIn("assets/.DS_Store", local)

    def test_records_sha256_and_size(self):
        write(self.root, "index.html", b"hello")
        self.assertEqual(deploy.collect_deploy_set(self.root), {"index.html": entry(b"hello")})

    def test_is_deploy_path(self):
        self.assertTrue(deploy.is_deploy_path("host.html"))
        self.assertTrue(deploy.is_deploy_path("assets/PhxPilots.JPG"))
        self.assertFalse(deploy.is_deploy_path("assets"))
        self.assertFalse(deploy.is_deploy_path("deploy/deploy.py"))
        self.assertFalse(deploy.is_deploy_path(".f3l-deploy-manifest.json"))
        self.assertFalse(deploy.is_deploy_path(""))


class PlanTest(unittest.TestCase):
    local = {
        "index.html": entry(b"home"),
        "styles.css": entry(b"css"),
        "assets/a.jpg": entry(b"jpeg"),
    }

    def manifest(self, **overrides):
        files = {rel: dict(info) for rel, info in self.local.items()}
        files.update(overrides)
        return {"version": 1, "files": files}

    def listing(self, **overrides):
        listing = {rel: info["size"] for rel, info in self.local.items()}
        listing[deploy.MANIFEST_NAME] = 100
        listing.update(overrides)
        return listing

    def test_no_manifest_makes_everything_new(self):
        plan = deploy.compute_plan(self.local, None, self.listing())
        self.assertEqual(plan.new, sorted(self.local))
        self.assertEqual(plan.changed + plan.unchanged + plan.remote_only, [])

    def test_manifest_without_files_counts_as_absent(self):
        plan = deploy.compute_plan(self.local, {"version": 1}, self.listing())
        self.assertEqual(plan.new, sorted(self.local))

    def test_everything_matching_is_unchanged(self):
        plan = deploy.compute_plan(self.local, self.manifest(), self.listing())
        self.assertEqual(plan.unchanged, sorted(self.local))
        self.assertEqual(plan.new + plan.changed + plan.remote_only, [])
        self.assertEqual(plan.to_upload, [])

    def test_path_missing_from_manifest_is_new(self):
        manifest = self.manifest()
        del manifest["files"]["styles.css"]
        plan = deploy.compute_plan(self.local, manifest, self.listing())
        self.assertEqual(plan.new, ["styles.css"])

    def test_path_missing_from_listing_is_new(self):
        listing = self.listing()
        del listing["assets/a.jpg"]
        plan = deploy.compute_plan(self.local, self.manifest(), listing)
        self.assertEqual(plan.new, ["assets/a.jpg"])
        self.assertEqual(plan.unchanged, ["index.html", "styles.css"])

    def test_hash_difference_is_changed(self):
        manifest = self.manifest(**{"index.html": {"sha256": "old", "size": 4}})
        plan = deploy.compute_plan(self.local, manifest, self.listing())
        self.assertEqual(plan.changed, ["index.html"])

    def test_remote_size_drift_behind_manifest_is_changed(self):
        plan = deploy.compute_plan(self.local, self.manifest(), self.listing(**{"styles.css": 999}))
        self.assertEqual(plan.changed, ["styles.css"])

    def test_force_marks_existing_files_changed(self):
        plan = deploy.compute_plan(self.local, self.manifest(), self.listing(), force=True)
        self.assertEqual(plan.changed, sorted(self.local))
        self.assertEqual(plan.unchanged, [])

    def test_remote_only_excludes_manifest_and_dotfiles(self):
        listing = self.listing(**{"old.html": 5, "assets/old/b.png": 3, ".htaccess": 9,
                                  "assets/.DS_Store": 1, "index.html.uploading": 2})
        plan = deploy.compute_plan(self.local, self.manifest(), listing)
        self.assertEqual(plan.remote_only, ["assets/old/b.png", "index.html.uploading", "old.html"])

    def test_upload_order_sends_assets_then_stylesheet_then_pages(self):
        plan = deploy.compute_plan(self.local, None, {})
        self.assertEqual(plan.to_upload, ["assets/a.jpg", "styles.css", "index.html"])

    def test_parent_dirs(self):
        self.assertEqual(deploy.parent_dirs("assets/highstart/a.png"), ["assets", "assets/highstart"])
        self.assertEqual(deploy.parent_dirs("index.html"), [])


class CredentialsTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.warnings = []

    def env_file(self, text, mode=0o600):
        path = self.dir / "deploy.env"
        path.write_text(text)
        path.chmod(mode)
        return path

    def resolve(self, environ, env_file=None, read_op=None):
        def no_op(ref):
            raise AssertionError("op read should not run")
        return deploy.resolve_settings(environ, env_file=env_file, warn=self.warnings.append,
                                       read_op=read_op or no_op)

    def test_parse_env_file(self):
        values = deploy.parse_env_file(
            "# comment\n\nF3L_FTP_HOST=ftp.example.com\nexport F3L_FTP_USER = 'bob'\n"
            'F3L_FTP_PASSWORD="p=a ss#word"\n'
        )
        self.assertEqual(values, {"F3L_FTP_HOST": "ftp.example.com", "F3L_FTP_USER": "bob",
                                  "F3L_FTP_PASSWORD": "p=a ss#word"})

    def test_parse_env_file_rejects_malformed_line(self):
        with self.assertRaises(deploy.UsageError):
            deploy.parse_env_file("F3L_FTP_HOST\n")

    def test_environment_beats_file_and_defaults_fill_the_rest(self):
        path = self.env_file("F3L_FTP_PASSWORD=from-file\nF3L_FTP_USER=file-user\n")
        s = self.resolve({"F3L_FTP_PASSWORD": "from-env"}, env_file=path)
        self.assertEqual((s.password, s.user, s.host, s.remote_dir),
                         ("from-env", "file-user", "ftp.mcneilco.com", "/f3l_series"))

    def test_file_used_when_environment_empty(self):
        path = self.env_file("F3L_FTP_PASSWORD=from-file\nF3L_FTP_REMOTE_DIR=/elsewhere\n")
        s = self.resolve({"F3L_FTP_PASSWORD": ""}, env_file=path)
        self.assertEqual((s.password, s.remote_dir), ("from-file", "/elsewhere"))

    def test_env_file_located_by_variable(self):
        path = self.env_file("F3L_FTP_PASSWORD=via-var\n")
        s = self.resolve({deploy.ENV_FILE_KEY: str(path)})
        self.assertEqual((s.password, s.env_file), ("via-var", path))

    def test_default_env_file_is_optional_but_explicit_one_is_not(self):
        with unittest.mock.patch.object(deploy, "DEFAULT_ENV_FILE", self.dir / "absent.env"):
            s = self.resolve({"F3L_FTP_PASSWORD": "x"})
        self.assertEqual(s.password, "x")
        with self.assertRaisesRegex(deploy.UsageError, "does not exist"):
            self.resolve({"F3L_FTP_PASSWORD": "x"}, env_file=self.dir / "absent.env")

    def test_op_reference_used_only_without_password(self):
        path = self.env_file("F3L_FTP_PASSWORD_OP_REF=op://Private/F3L FTP/password\n")
        refs = []
        s = self.resolve({}, env_file=path, read_op=lambda ref: refs.append(ref) or "from-op")
        self.assertEqual((s.password, refs), ("from-op", ["op://Private/F3L FTP/password"]))
        s = self.resolve({"F3L_FTP_PASSWORD": "from-env"}, env_file=path)
        self.assertEqual(s.password, "from-env")

    def test_missing_password_names_variable_and_file(self):
        path = self.env_file("F3L_FTP_USER=bob\n")
        with self.assertRaises(deploy.UsageError) as caught:
            self.resolve({}, env_file=path)
        self.assertIn("F3L_FTP_PASSWORD", str(caught.exception))
        self.assertIn(str(path), str(caught.exception))

    def test_warns_when_env_file_readable_by_others(self):
        self.resolve({}, env_file=self.env_file("F3L_FTP_PASSWORD=x\n", mode=0o644))
        self.assertEqual(len(self.warnings), 1)
        self.assertIn("chmod 600", self.warnings[0])
        self.warnings.clear()
        self.resolve({}, env_file=self.env_file("F3L_FTP_PASSWORD=x\n", mode=0o600))
        self.assertEqual(self.warnings, [])

    def test_password_not_in_repr(self):
        s = self.resolve({"F3L_FTP_PASSWORD": "hunter2"}, env_file=self.env_file(""))
        self.assertNotIn("hunter2", repr(s))


class GitStateTest(unittest.TestCase):
    def test_parse_porcelain_z_handles_renames_and_spaces(self):
        out = " M index.html\0R  assets/new name.jpg\0assets/old.jpg\0?? deploy/x.py\0"
        self.assertEqual(deploy.parse_porcelain_z(out),
                         ["index.html", "assets/new name.jpg", "assets/old.jpg", "deploy/x.py"])

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_dirty_reports_only_deploy_set_paths(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        make_site(root)
        git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["commit", "-qm", "site"], check=True)

        commit, dirty = deploy.git_state(root)
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertEqual(dirty, [])

        write(root, "README.txt", "not the site")
        write(root, "deploy/notes.md", "not the site")
        self.assertEqual(deploy.git_state(root)[1], [])

        write(root, "index.html", "edited")
        write(root, "assets/highstart/new image.png", b"png")
        self.assertEqual(deploy.git_state(root)[1],
                         ["assets/highstart/new image.png", "index.html"])

    def test_not_a_checkout_is_unknown(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        failed = subprocess.CompletedProcess([], 128, "", "not a git repository")
        self.assertEqual(deploy.git_state(root, run=lambda *a, **k: failed), (None, None))


class CliTest(unittest.TestCase):
    """main() end to end with a temp site and FakeRemote."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        make_site(self.root)
        self.environ = {"F3L_FTP_PASSWORD": "secret-pw", deploy.ENV_FILE_KEY: ""}
        self.git = lambda root: ("abc123", [])
        patcher = unittest.mock.patch.object(deploy, "DEFAULT_ENV_FILE", self.root / "absent.env")
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, argv, remote):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = deploy.main(argv, environ=self.environ, root=self.root,
                               remote_factory=lambda settings: remote, git=self.git)
        self.assertNotIn("secret-pw", out.getvalue() + err.getvalue())
        return code, out.getvalue(), err.getvalue()

    def deployed(self, remote):
        """A remote that already holds exactly the local site plus its manifest."""
        local = deploy.collect_deploy_set(self.root)
        for rel in local:
            remote.files[rel] = (self.root / rel).read_bytes()
        remote.files[deploy.MANIFEST_NAME] = json.dumps(
            deploy.build_manifest(local, "abc123", False, "t@host")).encode()
        return remote

    def test_dry_run_is_default_and_sends_nothing(self):
        remote = FakeRemote(files={"old.html": b"old"})
        code, out, _ = self.run_main([], remote)
        self.assertEqual(code, 0)
        self.assertEqual(remote.log, [])
        self.assertEqual(remote.files, {"old.html": b"old"})
        self.assertTrue(remote.closed)
        self.assertIn("DRY RUN", out)
        self.assertIn("New (6, would be uploaded)", out)
        self.assertIn("Remote-only (1, left alone; --delete removes them)", out)
        self.assertIn("Totals: 6 new, 0 changed, 0 unchanged, 1 remote-only", out)

    def test_dry_run_ignores_dirty_tree(self):
        self.git = lambda root: ("abc123", ["index.html"])
        code, out, _ = self.run_main([], FakeRemote())
        self.assertEqual(code, 0)
        self.assertIn("(dirty)", out)

    def test_first_upload_sends_everything_and_writes_manifest_last(self):
        remote = FakeRemote()
        code, out, _ = self.run_main(["--upload"], remote)
        self.assertEqual(code, 0, out)
        local = deploy.collect_deploy_set(self.root)
        self.assertEqual(remote.log[-1], ("manifest",))
        uploads = [e[1] for e in remote.log if e[0] == "upload"]
        self.assertEqual(uploads[-3:], ["styles.css", "about.html", "index.html"])
        self.assertIn("assets/highstart", remote.dirs)
        manifest = remote.read_manifest()
        self.assertEqual(manifest["files"], local)
        self.assertEqual((manifest["version"], manifest["git_commit"], manifest["git_dirty"]),
                         (1, "abc123", False))
        self.assertRegex(manifest["deployed_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertIn("@", manifest["deployed_by"])

    def test_second_run_after_upload_has_nothing_to_do(self):
        remote = FakeRemote()
        self.run_main(["--upload"], remote)
        remote.log.clear()
        code, out, _ = self.run_main(["--upload"], remote)
        self.assertEqual(code, 0)
        self.assertEqual(remote.log, [])
        self.assertIn("Nothing to do.", out)
        self.assertIn("Totals: 0 new, 0 changed, 6 unchanged", out)

    def test_one_page_edit_uploads_only_that_page(self):
        remote = self.deployed(FakeRemote())
        write(self.root, "about.html", "<h1>about, edited</h1>")
        code, out, _ = self.run_main(["--upload"], remote)
        self.assertEqual(code, 0)
        self.assertEqual(remote.log, [("upload", "about.html"), ("manifest",)])
        self.assertEqual(remote.files["about.html"], b"<h1>about, edited</h1>")
        self.assertIn("Changed (1, uploaded)", out)

    def test_force_resends_everything(self):
        remote = self.deployed(FakeRemote())
        code, _, _ = self.run_main(["--upload", "--force"], remote)
        self.assertEqual(code, 0)
        self.assertEqual(len([e for e in remote.log if e[0] == "upload"]), 6)

    def test_delete_removes_remote_only_files_only_when_asked(self):
        remote = self.deployed(FakeRemote(files={"old.html": b"old", ".htaccess": b"x"}))
        self.run_main(["--upload"], remote)
        self.assertIn("old.html", remote.files)
        code, _, _ = self.run_main(["--upload", "--delete"], remote)
        self.assertEqual(code, 0)
        self.assertNotIn("old.html", remote.files)
        self.assertIn(".htaccess", remote.files)
        self.assertIn(deploy.MANIFEST_NAME, remote.files)

    def test_failed_upload_leaves_old_manifest_and_exits_1(self):
        remote = self.deployed(FakeRemote())
        before = remote.files[deploy.MANIFEST_NAME]
        write(self.root, "index.html", "edited")
        write(self.root, "styles.css", "body{color:red}")
        remote.fail_on = "index.html"
        code, _, err = self.run_main(["--upload"], remote)
        self.assertEqual(code, 1)
        self.assertEqual(remote.files[deploy.MANIFEST_NAME], before)
        self.assertIn("manifest was not updated", err)
        self.assertTrue(remote.closed)

    def test_dirty_tree_refuses_upload_without_allow_dirty(self):
        self.git = lambda root: ("abc123", ["index.html"])
        remote = FakeRemote()
        code, _, err = self.run_main(["--upload"], remote)
        self.assertEqual(code, 2)
        self.assertIn("index.html", err)
        self.assertEqual(remote.log, [])

        code, _, _ = self.run_main(["--upload", "--allow-dirty"], remote)
        self.assertEqual(code, 0)
        self.assertTrue(remote.read_manifest()["git_dirty"])

    def test_unknown_git_state_refuses_upload(self):
        self.git = lambda root: (None, None)
        code, _, err = self.run_main(["--upload"], FakeRemote())
        self.assertEqual(code, 2)
        self.assertIn("git cannot report", err)

    def test_missing_password_exits_2_before_connecting(self):
        self.environ = {deploy.ENV_FILE_KEY: ""}
        remote = FakeRemote()
        code, _, err = self.run_main([], remote)
        self.assertEqual(code, 2)
        self.assertIn("F3L_FTP_PASSWORD", err)
        self.assertFalse(remote.closed)

    def test_settings_reach_the_remote_factory(self):
        self.environ.update(F3L_FTP_HOST="ftp.example.com", F3L_FTP_REMOTE_DIR="/site")
        seen = []
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            deploy.main([], environ=self.environ, root=self.root, git=self.git,
                        remote_factory=lambda s: seen.append(s) or FakeRemote())
        self.assertEqual((seen[0].host, seen[0].user, seen[0].remote_dir, seen[0].password),
                         ("ftp.example.com", "jmcneil", "/site", "secret-pw"))
        self.assertIn("ftp://jmcneil@ftp.example.com/site", out.getvalue())


class FakeFtp:
    """Just enough of ftplib.FTP for FtpRemote, over an in-memory tree."""

    def __init__(self, files=None, dirs=(), refuse_overwrite_rename=False):
        self.files = dict(files or {})
        self.dirs = {"/", "/f3l_series", *dirs}
        self.refuse_overwrite_rename = refuse_overwrite_rename
        self.commands = []
        self.cwd_path = "/"

    def _parent(self, path):
        return path.rsplit("/", 1)[0] or "/"

    def retrbinary(self, cmd, callback):
        path = cmd.split(" ", 1)[1]
        if path not in self.files:
            raise error_perm("550 No such file")
        callback(self.files[path])

    def storbinary(self, cmd, fh):
        path = cmd.split(" ", 1)[1]
        if self._parent(path) not in self.dirs:
            raise error_perm("550 No such directory")
        self.commands.append(("STOR", path))
        self.files[path] = fh.read()

    def rename(self, src, dst):
        if self.refuse_overwrite_rename and dst in self.files:
            raise error_perm("550 exists")
        self.commands.append(("RNFR/RNTO", src, dst))
        self.files[dst] = self.files.pop(src)

    def delete(self, path):
        self.commands.append(("DELE", path))
        del self.files[path]

    def mkd(self, path):
        if path in self.dirs:
            raise error_perm("550 exists")
        self.commands.append(("MKD", path))
        self.dirs.add(path)

    def cwd(self, path):
        if path not in self.dirs:
            raise error_perm("550 No such directory")
        self.cwd_path = path

    def mlsd(self, path, facts=()):
        yield ".", {"type": "cdir"}
        yield "..", {"type": "pdir"}
        for d in sorted(self.dirs):
            if d != path and self._parent(d) == path:
                yield d.rsplit("/", 1)[1], {"type": "dir"}
        for f, data in sorted(self.files.items()):
            if self._parent(f) == path:
                yield f.rsplit("/", 1)[1], {"type": "file", "size": str(len(data))}

    def quit(self):
        self.commands.append(("QUIT",))


class FtpRemoteTest(unittest.TestCase):
    def remote(self, ftp):
        remote = deploy.FtpRemote.__new__(deploy.FtpRemote)
        remote.ftp, remote.base, remote._dirs = ftp, "/f3l_series", {""}
        return remote

    def test_listing_walks_directories_with_sizes(self):
        ftp = FakeFtp(
            files={"/f3l_series/index.html": b"12345", "/f3l_series/assets/hs/a b.png": b"xy",
                   "/f3l_series/.f3l-deploy-manifest.json": b"{}", "/other/x.html": b"no"},
            dirs={"/f3l_series/assets", "/f3l_series/assets/hs", "/f3l_series/empty", "/other"},
        )
        self.assertEqual(self.remote(ftp).listing(), {
            ".f3l-deploy-manifest.json": 2, "assets/hs/a b.png": 2, "index.html": 5,
        })

    def test_upload_is_atomic_rename_over_target(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        path = write(root, "index.html", "new")
        ftp = FakeFtp(files={"/f3l_series/index.html": b"old"})
        self.remote(ftp).upload("index.html", path)
        self.assertEqual(ftp.commands, [
            ("STOR", "/f3l_series/index.html.uploading"),
            ("RNFR/RNTO", "/f3l_series/index.html.uploading", "/f3l_series/index.html"),
        ])
        self.assertEqual(ftp.files, {"/f3l_series/index.html": b"new"})

    def test_upload_falls_back_to_delete_when_rename_cannot_overwrite(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        path = write(root, "index.html", "new")
        ftp = FakeFtp(files={"/f3l_series/index.html": b"old"}, refuse_overwrite_rename=True)
        self.remote(ftp).upload("index.html", path)
        self.assertEqual(ftp.files, {"/f3l_series/index.html": b"new"})
        self.assertIn(("DELE", "/f3l_series/index.html"), ftp.commands)

    def test_manifest_round_trip_and_absent(self):
        ftp = FakeFtp()
        remote = self.remote(ftp)
        self.assertIsNone(remote.read_manifest())
        remote.write_manifest({"version": 1, "files": {}})
        self.assertEqual(remote.read_manifest(), {"version": 1, "files": {}})
        self.assertEqual(set(ftp.files), {"/f3l_series/.f3l-deploy-manifest.json"})

    def test_unreadable_manifest_counts_as_absent(self):
        ftp = FakeFtp(files={"/f3l_series/.f3l-deploy-manifest.json": b"not json"})
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(self.remote(ftp).read_manifest())
        self.assertIn("unreadable", err.getvalue())

    def test_mkdir_creates_once_and_tolerates_existing(self):
        ftp = FakeFtp(dirs={"/f3l_series/assets"})
        remote = self.remote(ftp)
        remote.mkdir("assets")
        remote.mkdir("assets/highstart")
        remote.mkdir("assets/highstart")
        self.assertEqual(ftp.commands, [("MKD", "/f3l_series/assets/highstart")])
        self.assertEqual(ftp.cwd_path, "/f3l_series")

    def test_execute_plan_against_ftp_remote_creates_nested_dirs(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        make_site(root)
        local = deploy.collect_deploy_set(root)
        ftp = FakeFtp()
        remote = self.remote(ftp)
        plan = deploy.compute_plan(local, remote.read_manifest(), remote.listing())
        deploy.execute_plan(plan, root, remote, deploy.build_manifest(local, "c", False, "t"),
                            log=lambda msg: None)
        self.assertEqual(
            set(remote.listing()),
            set(local) | {deploy.MANIFEST_NAME},
        )
        self.assertFalse(any(p.endswith(deploy.UPLOAD_SUFFIX) for p in ftp.files))

    def test_missing_remote_dir_is_refused_not_created(self):
        ftp = FakeFtp()
        with unittest.mock.patch.object(deploy, "FTP", return_value=ftp):
            ftp.connect = ftp.login = ftp.set_pasv = ftp.set_debuglevel = lambda *a: None
            ftp.pwd = lambda: ftp.cwd_path
            with self.assertRaisesRegex(deploy.UsageError, "refusing to create"):
                deploy.FtpRemote("h", "u", "p", "/f3l_seires")
            self.assertEqual(deploy.FtpRemote("h", "u", "p", "/f3l_series").base, "/f3l_series")
        self.assertNotIn("/f3l_seires", ftp.dirs)


if __name__ == "__main__":
    unittest.main()
