#!/usr/bin/env python3
"""Build a NoCloud cloud-init ISO (volume label: cidata) using pycdlib.

Usage: python make_iso.py <source-dir> <output.iso>
Source dir must contain user-data, meta-data and network-config.
"""
import os
import sys

import pycdlib


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    src, dst = sys.argv[1], sys.argv[2]
    iso = pycdlib.PyCdlib()
    iso.new(
        interchange_level=3,
        joliet=3,
        rock_ridge="1.09",
        vol_ident="cidata",
    )

    for name in ("user-data", "meta-data", "network-config"):
        path = os.path.join(src, name)
        if not os.path.exists(path):
            continue
        iso.add_file(
            path,
            f"/{name.upper().replace('-', '_')}.;1",
            rr_name=name,
            joliet_path=f"/{name}",
        )

    if os.path.exists(dst):
        os.remove(dst)
    iso.write(dst)
    iso.close()
    print(f"ISO written: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
