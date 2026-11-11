"""Embed the requirement-test vectors and the field cycles in C (exact float32 values, hex literals).

The values are the float32 casts of the same decimals that the SIL harness reads with fscanf + (float),
so the target sees bit-identical inputs. Usage: python gen_vectors.py <out_dir>
Writes vectors.h, vectors.c and vectors.json (order and names of the vectors).
"""
import json
import pathlib
import sys

import numpy as np

import common
import stages


def read_vec(path):
    lines = pathlib.Path(path).read_text().split("\n")
    n, ov = lines[0].split()
    rows = np.array([[float(x) for x in l.split()] for l in lines[1:1 + int(n)]])
    return float(ov), rows[:, 0], rows[:, 1]


def f32hex(a):
    return ", ".join(float(np.float32(x)).hex() + "f" for x in a)


def main(out):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    spec = common.load_spec(common.ROOT / "spec" / "baseline.json")
    tests, field = stages.prepare_vectors(spec)
    names = [t["name"] for t in tests] + [f"field_{n}" for n in field]
    body, table = [], []
    for k, name in enumerate(names):
        ov, I, V = read_vec(stages.VEC / f"{name}.txt")
        body.append(f"static const float I{k}[{len(I)}] = {{{f32hex(I)}}};")
        body.append(f"static const float V{k}[{len(V)}] = {{{f32hex(V)}}};")
        table.append(f"    {{{len(I)}u, {float(np.float32(ov)).hex()}f, I{k}, V{k}}}, /* {name} */")
    (out / "vectors.h").write_text(
        "#ifndef VECTORS_H\n#define VECTORS_H\n#include <stdint.h>\n"
        "typedef struct { uint32_t n; float override; const float *I; const float *V; } pil_vector_t;\n"
        f"#define PIL_N_VECTORS {len(names)}u\nextern const pil_vector_t PIL_VECTORS[PIL_N_VECTORS];\n#endif\n")
    (out / "vectors.c").write_text('#include "vectors.h"\n' + "\n".join(body) +
                                   "\nconst pil_vector_t PIL_VECTORS[PIL_N_VECTORS] = {\n" + "\n".join(table) + "\n};\n")
    (out / "vectors.json").write_text(json.dumps(names))
    print(len(names), "vectors,", sum(len(read_vec(stages.VEC / f"{n}.txt")[1]) for n in names), "rows")


if __name__ == "__main__":
    main(sys.argv[1])
