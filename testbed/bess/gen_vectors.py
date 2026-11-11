"""Embed the requirement-test vectors of subject 3 in C (exact float32 values, hex literals).

Values are the float32 casts of the same decimals the SIL harness reads (fscanf %lf + (float)), so the
target sees bit-identical inputs. The field vector (390,859 rows x 3 inputs) does not fit in 1 MB of flash and
are NOT embedded: the field oracle runs on the QEMU build (stages.field).
Usage: python gen_vectors.py <out_dir>  -> vectors.h, vectors.c, vectors.json
"""
import json
import pathlib
import sys

import numpy as np

import common
import stages

FIELDS = ("rst", "cur", "tref")


def read_vec(path):
    lines = pathlib.Path(path).read_text().split("\n")
    n = int(lines[0])
    return np.array([[float(x) for x in l.split()] for l in lines[1:1 + n]])


def f32hex(a):
    return ", ".join(float(np.float32(x)).hex() + "f" for x in a)


def main(out):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    spec = common.load_spec(common.ROOT / "spec" / "baseline.json")
    tests, _ = stages.prepare_vectors(spec)
    names = [t["name"] for t in tests]
    body, table, rows = [], [], 0
    for k, name in enumerate(names):
        a = read_vec(stages.VEC / f"{name}.txt")
        rows += len(a)
        for c, fld in enumerate(FIELDS):
            body.append(f"static const float {fld}{k}[{len(a)}] = {{{f32hex(a[:, c])}}};")
        table.append(f"    {{{len(a)}u, " + ", ".join(f"{fld}{k}" for fld in FIELDS) + f"}}, /* {name} */")
    (out / "vectors.h").write_text(
        "#ifndef VECTORS_H\n#define VECTORS_H\n#include <stdint.h>\n"
        "typedef struct { uint32_t n; const float *rst, *cur, *tref; } pil_vector_t;\n"
        f"#define PIL_N_VECTORS {len(names)}u\nextern const pil_vector_t PIL_VECTORS[PIL_N_VECTORS];\n#endif\n")
    (out / "vectors.c").write_text('#include "vectors.h"\n' + "\n".join(body) +
                                   "\nconst pil_vector_t PIL_VECTORS[PIL_N_VECTORS] = {\n" + "\n".join(table) + "\n};\n")
    (out / "vectors.json").write_text(json.dumps(names))
    print(len(names), "vectors,", rows, "rows")


if __name__ == "__main__":
    main(sys.argv[1])
