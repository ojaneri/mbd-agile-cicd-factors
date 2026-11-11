"""Parse the real-target PIL serial stream (see harness/stm32l4/pil_main.c) and verify integrity.

parse(text, names) -> dict name -> dict(out=np.array(float32 values), n_ok, crc_ok, max_cycles, total_cycles)
A vector whose line count or CRC32 does not match is marked crc_ok=False (re-run it; never use it).
"""
import struct
import zlib

import numpy as np


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
            bits = [int(h, 16) for h in vals]
            data = b"".join(struct.pack("<I", b) for b in bits)
            ok = int(idx) == cur and len(bits) == n_exp and (zlib.crc32(data) & 0xFFFFFFFF) == int(crc, 16)
            out = np.array([struct.unpack("<f", struct.pack("<I", b))[0] for b in bits], dtype=np.float64)
            res[names[cur]] = dict(out=out, n_ok=len(bits) == n_exp, crc_ok=ok,
                                   max_cycles=int(cmax), total_cycles=int(ctot))
            cur = None
        elif cur is not None and len(line) == 8:
            try:
                int(line, 16)
                vals.append(line)
            except ValueError:
                pass  # a corrupted line; the CRC check will reject the vector
    return res
