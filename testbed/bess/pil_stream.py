"""Parse the subject-3 real-target PIL stream (harness/stm32l4/pil_main.c) and verify integrity.

parse(text, names) -> dict name -> dict(te, der (np arrays of float32 values), n_ok, crc_ok,
max_cycles, total_cycles). A vector whose line count or CRC32 does not match is crc_ok=False.
"""
import struct
import zlib

import numpy as np


def _f(b):
    return struct.unpack("<f", struct.pack("<I", b))[0]


def parse(text, names):
    res, cur, vals = {}, None, []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("@T "):
            _, idx, n = line.split()
            cur, vals, n_exp = int(idx), [], int(n)
        elif line.startswith("@S ") and cur is not None:
            parts = line.split()
            if len(parts) != 5:
                cur = None
                continue
            _, idx, crc, cmax, ctot = parts
            data = b"".join(struct.pack("<II", r, v) for r, v in vals)
            ok = int(idx) == cur and len(vals) == n_exp and (zlib.crc32(data) & 0xFFFFFFFF) == int(crc, 16)
            res[names[cur]] = dict(te=np.array([_f(r) for r, _ in vals]), der=np.array([_f(v) for _, v in vals]),
                                   n_ok=len(vals) == n_exp, crc_ok=ok, max_cycles=int(cmax), total_cycles=int(ctot))
            cur = None
        elif cur is not None and len(line) == 17 and line[8] == " ":
            try:
                vals.append((int(line[:8], 16), int(line[9:], 16)))
            except ValueError:
                pass  # corrupted line; the CRC check rejects the vector
    return res
