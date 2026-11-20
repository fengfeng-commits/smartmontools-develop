#!/usr/bin/env python3
"""Create and populate the GitHub repository for this project.

Needs a personal access token in the GH_TOKEN (or GITHUB_TOKEN) environment
variable with `repo` scope. The token is never written to disk or printed.

Usage:
    set GH_TOKEN=...            (Windows cmd)
    $env:GH_TOKEN = "..."       (PowerShell, this session only)
    python scripts/create_repo.py [--name smartmontools-develop] [--dry-run]

Idempotent: an existing repository is reused, existing files are updated.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
DESCRIPTION = ("Unofficial smartmontools branch: Windows installer and macOS dmg "
               "rebuilt with branding patches. Project home: https://smartmontools.cn")
TOPICS = ["smartmontools", "smartctl", "smartd", "smart", "disk-health",
          "windows", "macos", "gplv2", "unofficial-build"]
SKIP_DIRS = {".git", "__pycache__", "dist", "out"}
SKIP_EXT = {".exe", ".dmg", ".zip", ".pkg", ".pyc"}


def token():
    t = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not t:
        sys.exit("GH_TOKEN is not set. Export a token with `repo` scope first.")
    return t


def call(method, path, tok, payload=None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "dsh-agent")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        return e.code, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="smartmontools-develop")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tok = token()
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    status, me = call("GET", "/user", tok)
    if status != 200:
        sys.exit("cannot authenticate (%s): %s" % (status, me))
    owner = me["login"]
    print("authenticated as:", owner)

    status, _ = call("GET", "/repos/%s/%s" % (owner, args.name), tok)
    if status == 200:
        print("repository already exists: %s/%s" % (owner, args.name))
    elif args.dry_run:
        print("[dry-run] would create %s/%s" % (owner, args.name))
    else:
        status, res = call("POST", "/user/repos", tok, {
            "name": args.name,
            "description": DESCRIPTION,
            "private": False,
            "has_issues": True,
            "has_wiki": False,
            "has_projects": False,
            "auto_init": False,
        })
        if status not in (200, 201):
            sys.exit("create failed (%s): %s" % (status, res))
        print("created:", res["html_url"])

    files = []
    for root, dirs, names in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if os.path.splitext(n)[1].lower() in SKIP_EXT:
                continue
            full = os.path.join(root, n)
            rel = os.path.relpath(full, repo_root).replace(os.sep, "/")
            files.append((rel, full))
    files.sort()

    for rel, full in files:
        with open(full, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        # Fetch existing sha so updates overwrite instead of failing.
        status, cur = call("GET", "/repos/%s/%s/contents/%s" % (owner, args.name, rel), tok)
        sha = cur.get("sha") if status == 200 and isinstance(cur, dict) else None
        payload = {"message": "Add %s" % rel, "content": content}
        if sha:
            payload["sha"] = sha
            payload["message"] = "Update %s" % rel
        if args.dry_run:
            print("[dry-run] %s %s" % ("update" if sha else "add", rel))
            continue
        status, res = call("PUT", "/repos/%s/%s/contents/%s" % (owner, args.name, rel), tok, payload)
        if status not in (200, 201):
            print("FAILED %s (%s): %s" % (rel, status, res))
        else:
            print("%s %s" % ("updated" if sha else "added", rel))

    if args.dry_run:
        print("[dry-run] would set description and topics")
        return

    call("PATCH", "/repos/%s/%s" % (owner, args.name), tok, {
        "description": DESCRIPTION,
        "homepage": "https://smartmontools.cn",
    })
    call("PUT", "/repos/%s/%s/topics" % (owner, args.name), tok, {"names": TOPICS})
    print("repository:", "https://github.com/%s/%s" % (owner, args.name))


if __name__ == "__main__":
    main()
