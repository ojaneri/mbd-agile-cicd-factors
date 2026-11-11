"""E5 vectors: the subject's requirement-test vectors only (no field cycles), via its own gen_vectors.
Usage (WSL): python gen_vec_e5.py <subject_dir> <out_dir>"""
import sys

sys.path.insert(0, sys.argv[1])
import gen_vectors  # noqa: E402
import stages  # noqa: E402

_orig = stages.prepare_vectors
stages.prepare_vectors = lambda spec: (_orig(spec)[0], {})
gen_vectors.main(sys.argv[2])
