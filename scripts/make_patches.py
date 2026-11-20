#!/usr/bin/env python3
"""Regenerate patches/ from an unmodified upstream smartmontools source tree.

Usage:
    python scripts/make_patches.py <path-to-upstream-src>

Only display strings are touched. Identifiers that the uninstaller, the
registry keys and the install path depend on are deliberately left alone:
changing them breaks upgrades and leaves orphaned entries behind.
"""

import difflib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUTDIR = os.path.join(REPO, "patches")

BRAND = "SmartmonTools Develop"
HOLDER = "(C) 2002-@YY@, Bruce Allen, Christian Franke, www.smartmontools.org"

# (relative path, [(old, new), ...])
EDITS = [
    (
        "os_win32/versioninfo.rc.in",
        [
            ('            VALUE "CompanyName", "www.smartmontools.org"',
             '            VALUE "CompanyName", "%s"' % BRAND),
            ('            VALUE "LegalCopyright", "%s"' % HOLDER,
             '            VALUE "LegalCopyright", "%s; modifications (C) 2026 %s"' % (HOLDER, BRAND)),
            ('            VALUE "ProductName", "smartmontools"',
             '            VALUE "ProductName", "%s"' % BRAND),
        ],
    ),
    (
        "os_win32/installer.nsi",
        [
            # Upstream only ships Unicode installers, but the script has no
            # explicit switch; without this makensis defaults to an ANSI
            # installer which mangles non-ASCII paths. Must precede Name/OutFile.
            ('!ifndef INPDIR', 'Unicode true\n\n!ifndef INPDIR'),
            ('Name "smartmontools"',
             'Name "%s"' % BRAND),
            ('  VIAddVersionKey /LANG=1033-English "CompanyName" "www.smartmontools.org"',
             '  VIAddVersionKey /LANG=1033-English "CompanyName" "%s"' % BRAND),
            ('  VIAddVersionKey /LANG=1033-English "LegalCopyright" "(C) 2002-20${YY}, Bruce Allen, Christian Franke, www.smartmontools.org"',
             '  VIAddVersionKey /LANG=1033-English "LegalCopyright" "(C) 2002-20${YY}, Bruce Allen, Christian Franke, www.smartmontools.org; modifications (C) 2026 %s"' % BRAND),
            ('  VIAddVersionKey /LANG=1033-English "ProductName" "smartmontools"',
             '  VIAddVersionKey /LANG=1033-English "ProductName" "%s"' % BRAND),
            ('  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\smartmontools" "DisplayName" "smartmontools"',
             '  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\smartmontools" "DisplayName" "%s"' % BRAND),
        ],
    ),
]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SM_SRC", "")
    if not src or not os.path.isdir(src):
        sys.exit("usage: make_patches.py <path-to-upstream-src>")
    if not os.path.isfile(os.path.join(src, "configure.ac")):
        sys.exit("not a smartmontools source tree: %s" % src)

    os.makedirs(OUTDIR, exist_ok=True)
    for old_file in os.listdir(OUTDIR):
        if old_file.endswith(".patch"):
            os.remove(os.path.join(OUTDIR, old_file))

    seq = 0
    for rel, pairs in EDITS:
        path = os.path.join(src, rel)
        with open(path, "r", encoding="utf-8", newline="") as f:
            original = f.read()
        text = original
        for old, new in pairs:
            if text.count(old) != 1:
                sys.exit("%s: expected exactly one match, found %d for:\n%s"
                         % (rel, text.count(old), old))
            text = text.replace(old, new)
        if text == original:
            sys.exit("%s: nothing changed" % rel)

        seq += 1
        name = "%04d-brand-%s.patch" % (seq, os.path.basename(rel).replace(".", "-"))
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            text.splitlines(keepends=True),
            fromfile="a/" + rel,
            tofile="b/" + rel,
            n=3,
        )
        body = "".join(diff)
        with open(os.path.join(OUTDIR, name), "w", encoding="utf-8", newline="") as f:
            f.write(body)
        print("wrote %s (%d bytes)" % (name, len(body)))


if __name__ == "__main__":
    main()
