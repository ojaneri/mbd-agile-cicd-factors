"""Toolchain smoke test: simulate the exported FMU with FMPy (MIL stage check).

Prints the final SoC and terminal voltage and compares SoC with the analytic value
soc(t) = 1 - I*t/Q for constant current. This checks the chain, not any paper claim.
"""
import sys
from fmpy import simulate_fmu, read_model_description

fmu = sys.argv[1] if len(sys.argv) > 1 else "SmokeRC.fmu"
md = read_model_description(fmu)
print("FMI", md.fmiVersion, "| ME:", md.modelExchange is not None, "| CS:", md.coSimulation is not None)

t_end = 600.0
res = simulate_fmu(fmu, stop_time=t_end, output=["soc", "v"], start_values={"I": 1.5})
soc_end, v_end = res["soc"][-1], res["v"][-1]
soc_ref = 1.0 - 1.5 * t_end / (3.0 * 3600)
print(f"soc(end)={soc_end:.6f} analytic={soc_ref:.6f} abs_err={abs(soc_end - soc_ref):.2e}")
print(f"v(end)={v_end:.6f}")
sys.exit(0 if abs(soc_end - soc_ref) < 1e-4 else 1)
