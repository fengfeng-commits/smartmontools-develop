#!/usr/bin/env python3
"""Apply patches/ to a pristine source tree and write the result elsewhere.

This is a minimal stand-in for `git apply` for hosts without git. It refuses
to guess: any hunk whose context does not match exactly is a hard failure.

Usage:
    python scripts/apply_patches.py <src-tree> <dst-tree>
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATCHDIR = os.path.join(os.path.dirname(HERE), "patches")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def apply_one(patch_path, src_root, dst_root):
    with open(patch_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    target = None
    src = None
    out = []
    cursor = 0
    applied = 0
    i = 0

    def flush():
        if target is None:
            return
        dest = os.path.join(dst_root, target)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="") as fh:
            fh.write("\n".join(out) + "\n")

    while i < len(lines):
        line = lines[i]
        if line.startswith("--- a/"):
            flush()
            target = line[6:]
            path = os.path.join(src_root, target)
            with open(path, encoding="utf-8") as fh:
                src = fh.read().splitlines()
            out = []
            cursor = 0
            i += 1
            continue
        if line.startswith("+++ b/"):
            i += 1
            continue

        m = HUNK.match(line)
        if not m or src is None:
            i += 1
            continue

        start = int(m.group(1))
        body = []
        j = i + 1
        while j < len(lines) and not lines[j].startswith("@@ ") and not lines[j].startswith("--- a/"):
            body.append(lines[j])
            j += 1

        out.extend(src[cursor:start - 1])
        cursor = start - 1
        for bl in body:
            if bl == "":
                sys.exit("%s: bare empty line in hunk — patch is corrupt" % patch_path)
            tag, content = bl[0], bl[1:]
            if tag == " ":
                if src[cursor] != content:
                    sys.exit("%s: context mismatch at line %d\n  want: %r\n  got : %r"
                             % (target, cursor + 1, content, src[cursor]))
                out.append(content)
                cursor += 1
            elif tag == "-":
                if src[cursor] != content:
                    sys.exit("%s: removal mismatch at line %d\n  want: %r\n  got : %r"
                             % (target, cursor + 1, content, src[cursor]))
                cursor += 1
            elif tag == "+":
                out.append(content)
            else:
                sys.exit("%s: unexpected hunk line %r" % (patch_path, bl))
        applied += 1
        i = j

    out.extend(src[cursor:])
    flush()
    return applied


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: apply_patches.py <src-tree> <dst-tree>")
    src_root, dst_root = sys.argv[1], sys.argv[2]
    if not os.path.isfile(os.path.join(src_root, "configure.ac")):
        sys.exit("not a smartmontools source tree: %s" % src_root)

    names = sorted(n for n in os.listdir(PATCHDIR) if n.endswith(".patch"))
    total = 0
    for name in names:
        hunks = apply_one(os.path.join(PATCHDIR, name), src_root, dst_root)
        total += hunks
        print("applied %s (%d hunk(s))" % (name, hunks))
    print("%d hunk(s) applied -> %s" % (total, dst_root))


if __name__ == "__main__":
    main()
