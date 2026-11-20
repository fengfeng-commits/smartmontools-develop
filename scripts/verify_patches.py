#!/usr/bin/env python3
"""Verify that patches/ actually applies to a pristine upstream source tree.

Stands in for `git apply --check`, which is unavailable on hosts without git.
Checks each hunk's context and removed lines against the target file, and
rejects the two mistakes that make a patch unappliable:

  * a bare empty line inside a hunk (must be a single space)
  * a hunk whose context does not match at the stated line number

Usage:
    python scripts/verify_patches.py <path-to-upstream-src>
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATCHDIR = os.path.join(os.path.dirname(HERE), "patches")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def main():
    src_root = sys.argv[1] if len(sys.argv) > 1 else ""
    if not src_root or not os.path.isdir(src_root):
        sys.exit("usage: verify_patches.py <path-to-upstream-src>")

    names = sorted(n for n in os.listdir(PATCHDIR) if n.endswith(".patch"))
    if not names:
        sys.exit("no patches found in %s" % PATCHDIR)

    errors = 0
    for name in names:
        with open(os.path.join(PATCHDIR, name), encoding="utf-8") as f:
            raw = f.read()
        if not raw.endswith("\n"):
            print("FAIL %s: missing trailing newline" % name)
            errors += 1
        lines = raw.splitlines()

        target = None
        cursor = 0
        i = 0
        hunks = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("--- a/"):
                target = line[6:]
                i += 1
                continue
            if line.startswith("+++ b/"):
                i += 1
                continue
            m = HUNK.match(line)
            if not m:
                i += 1
                continue
            hunks += 1
            start = int(m.group(1))
            if not target:
                print("FAIL %s: hunk before file header" % name)
                errors += 1
                break
            path = os.path.join(src_root, target)
            if not os.path.isfile(path):
                print("FAIL %s: target missing %s" % (name, target))
                errors += 1
                break
            with open(path, encoding="utf-8") as f:
                src = f.read().splitlines()

            j = i + 1
            body = []
            while j < len(lines) and not lines[j].startswith("@@ ") and not lines[j].startswith("--- a/"):
                body.append(lines[j])
                j += 1

            k = start - 1
            for bl in body:
                if bl == "":
                    print("FAIL %s: bare empty line inside hunk near line %d (must start with a space)"
                          % (name, k + 1))
                    errors += 1
                    k += 1
                    continue
                tag, content = bl[0], bl[1:]
                if tag == "+":
                    continue
                if tag not in (" ", "-"):
                    print("FAIL %s: unexpected hunk line %r" % (name, bl))
                    errors += 1
                    continue
                if k >= len(src):
                    print("FAIL %s: line %d past end of %s" % (name, k + 1, target))
                    errors += 1
                    k += 1
                    continue
                if src[k] != content:
                    print("FAIL %s: %s line %d\n  expected: %r\n  found   : %r"
                          % (name, target, k + 1, content, src[k]))
                    errors += 1
                k += 1
            i = j
            cursor = k

        if hunks == 0:
            print("FAIL %s: no hunks" % name)
            errors += 1
        else:
            print("ok   %s (%d hunk(s), target %s)" % (name, hunks, target))

    if errors:
        sys.exit("%d problem(s)" % errors)
    print("all patches apply cleanly")


if __name__ == "__main__":
    main()
