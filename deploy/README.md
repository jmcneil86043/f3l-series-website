# Preview and deploy

Two tools for the F3L Contest Series site (www.f3lcontestseries.org). Both work from any checkout
or worktree with no arguments. They need Python 3.9+ and nothing else.

- `deploy/preview.sh`: serves this checkout on localhost so you can look at it before it goes live.
- `deploy/deploy.py`: publishes the site over FTP and sends only the files that changed. By
  default it does a **dry run**: it prints the plan and sends nothing.

These replace the VS Code upload-on-save sync (`smartftp.json`). The deploy runs from Bishop or
John's Mac, started by hand or by a step worker. No GitHub Action is involved; the reason is in
`decisions/F3L-Series-Web-Site-decisions.md` § Repo and runtime.

## Preview

```sh
deploy/preview.sh          # http://127.0.0.1:8080/
deploy/preview.sh 8081     # another port
```

The script serves the checkout as it is, uncommitted edits included. There is no build step,
and every link in the site is relative, so pages, images and the bulletin download all work.
Stop it with Ctrl-C.

**Reviewing a worktree on Bishop from your Mac.** Start the preview on Bishop inside the
worktree, then forward the port:

```sh
ssh -L 8080:127.0.0.1:8080 bishop     # leave this open
```

Then open http://localhost:8080/ on the Mac. The server only listens on 127.0.0.1, so the tunnel
is the only way in. (VS Code Remote-SSH forwards the port automatically when the preview starts
in its terminal.)

## First-time setup on the deploying machine

Do this once per machine that will deploy. The file lives outside the repo, so every worktree
shares it and it can't be committed.

```sh
mkdir -p ~/.config/f3l-series-website
cp deploy/deploy.env.example ~/.config/f3l-series-website/deploy.env
chmod 600 ~/.config/f3l-series-website/deploy.env
```

Edit it and set **one** of:

- `F3L_FTP_PASSWORD=` followed by the FTP password (the `password` in your local `smartftp.json`), or
- `F3L_FTP_PASSWORD_OP_REF=op://<vault>/<item>/password`, a 1Password reference. The deploy runs
  `op read` on it, so the 1Password CLI must be installed and signed in on that machine. Check
  it with `op read "op://<vault>/<item>/password"` first.

Host `ftp.mcneilco.com`, user `jmcneil` and remote dir `/f3l_series` are the defaults, so you only
need to set them if they change.

For each setting, deploy.py uses the first source that has it:

1. the process environment (`F3L_FTP_HOST`, `F3L_FTP_USER`, `F3L_FTP_PASSWORD`, `F3L_FTP_REMOTE_DIR`, `F3L_FTP_PASSWORD_OP_REF`);
2. the env file: `--env PATH`, else `$F3L_DEPLOY_ENV`, else `~/.config/f3l-series-website/deploy.env`;
3. for the password only, `op read` on `F3L_FTP_PASSWORD_OP_REF`;
4. the defaults above (never the password).

The script reads the env file as `KEY=value` lines and never runs it through a shell. It warns if
other users can read the file. It never prints the password, writes it to disk or passes it on a
command line. A `deploy/deploy.env` inside the repo is gitignored as a backstop, but keep the real
file in `~/.config`.

## Deploy

```sh
deploy/deploy.py                          # dry run: show the plan, send nothing
deploy/deploy.py --upload                 # publish new and changed files
```

A dry run connects and reads the server, then prints every file under one of these headings:

- **New**: not on the server yet, or not in the server's manifest
- **Changed**: its content differs from what was last deployed, or someone changed it on the server since
- **Unchanged**: skipped
- **Remote-only**: on the server but not in the repo; left alone unless you pass `--delete`

Totals follow. Run the dry run, read it, then run the same command with `--upload`.

Other flags:

| Flag | Effect |
|---|---|
| `--force` | re-send every file and rebuild the manifest |
| `--delete` | also delete remote-only files (never directories, never dotfiles such as `.htaccess`) |
| `--allow-dirty` | allow `--upload` when site files have uncommitted changes |
| `--env PATH` | use this env file |
| `--verbose` | log the FTP commands (ftplib masks the password) |

Exit codes: 0 means success, including a dry run. 1 means an FTP failure. 2 means a usage
problem: missing password, bad env file, uncommitted site files, or a remote dir that doesn't
exist.

### What gets published

- every `*.html` at the repo root
- `styles.css`
- everything under `assets/`

Nothing whose name starts with `.` is published. Everything else stays local: `README.txt`,
`deploy/`, `decisions/`, step folders and `smartftp.json`. The list is at the top of `deploy.py`.

### How it decides what changed

Git gives files fresh timestamps, and FTP has no checksum command. So the script keeps its own
manifest on the server at `/f3l_series/.f3l-deploy-manifest.json`. The manifest records each
file's sha256 and size, plus the commit, the time, who deployed, and whether the tree was dirty.
It is also the audit trail. To see what is live:

```sh
curl -s http://www.f3lcontestseries.org/.f3l-deploy-manifest.json | head
```

### Safety

- Upload is opt-in. A command without `--upload` never changes the server.
- `--upload` refuses when site files have uncommitted changes, so what ships matches a commit.
- Each file goes up as `<name>.uploading` and is then renamed over the old one, so visitors never
  get a half-sent page. Assets go first, then `styles.css`, then pages.
- The manifest is written last. If a run fails partway, the old manifest stays, and the next run
  re-sends whatever didn't finish.
- The script won't create the remote dir. A mistyped `F3L_FTP_REMOTE_DIR` fails instead of
  publishing to the wrong place.
- The host only offers plain FTP (`AUTH TLS` is refused), so the password crosses the network in
  the clear, just as it did with the VS Code sync.

## Tests

```sh
python3 -m unittest discover -s deploy/tests
```

The tests use a fake FTP server and don't touch the network.

## Acceptance checklist (first live run)

1. `deploy/preview.sh`, then open the site: every page loads, images show, and on "Host a Contest"
   the bulletin template downloads.
2. With no env file and no `F3L_FTP_*` variables, `deploy/deploy.py` exits 2 with a one-line
   message about the missing password. It doesn't prompt.
3. With the env file in place, `deploy/deploy.py` connects. The first time it says there is no
   manifest and lists every file as new. Any remote-only leftovers are listed but not touched.
4. `deploy/deploy.py --upload` sends everything and writes the manifest. The live site still renders.
5. `deploy/deploy.py` again: 0 new, 0 changed.
6. Edit one page, commit, and run `deploy/deploy.py --upload`. Only that page is sent, and the live
   site shows the edit. A dry run straight afterwards shows nothing to send.
7. `git log -p | grep -E '^\+F3L_FTP_PASSWORD=.'` finds nothing, and `git status` doesn't list
   `smartftp.json`.
