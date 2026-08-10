#!/usr/bin/env python3
"""Compile po/<lang>.po into locale/<lang>/LC_MESSAGES/log-samba-audit.mo.

Uses only the standard library (Tools/i18n/msgfmt.py logic) so no external
gettext tools are required. Run this after editing translations:
    python3 build_locale.py
"""
import os
import ast
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "log-samba-audit"


def parse_po(path):
    """Return {msgid: msgstr} from a .po file (simple, no plurals/contexts)."""
    messages = {}
    msgid = msgstr = None
    mode = None  # "id" | "str"

    def flush():
        if msgid is not None and msgstr:
            messages[msgid] = msgstr

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("msgid "):
                flush()
                msgid = ast.literal_eval(line[len("msgid "):])
                msgstr = ""
                mode = "id"
            elif line.startswith("msgstr "):
                msgstr = ast.literal_eval(line[len("msgstr "):])
                mode = "str"
            elif line.startswith('"'):
                chunk = ast.literal_eval(line)
                if mode == "id":
                    msgid += chunk
                elif mode == "str":
                    msgstr += chunk
    flush()
    return messages


def make_mo(messages):
    """Serialize messages dict into .mo binary format."""
    keys = sorted(messages.keys())
    offsets = []
    ids = b""
    strs = b""
    for k in keys:
        v = messages[k]
        kb = k.encode("utf-8")
        vb = v.encode("utf-8")
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b"\x00"
        strs += vb + b"\x00"
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    output = struct.pack("Iiiiiii", 0x950412de, 0, len(keys),
                         7 * 4, 7 * 4 + len(keys) * 8, 0, 0)
    output += struct.pack("i" * len(koffsets), *koffsets)
    output += struct.pack("i" * len(voffsets), *voffsets)
    output += ids
    output += strs
    return output


def main():
    po_dir = os.path.join(HERE, "po")
    built = 0
    for fn in os.listdir(po_dir):
        if not fn.endswith(".po"):
            continue
        lang = fn[:-3]
        messages = parse_po(os.path.join(po_dir, fn))
        out_dir = os.path.join(HERE, "locale", lang, "LC_MESSAGES")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, DOMAIN + ".mo")
        with open(out, "wb") as f:
            f.write(make_mo(messages))
        print("built %s (%d strings) -> %s" % (fn, len(messages), out))
        built += 1
    if not built:
        print("no .po files found in", po_dir)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
