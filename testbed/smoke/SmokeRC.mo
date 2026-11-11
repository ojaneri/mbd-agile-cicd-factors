// Toolchain smoke test only. Not a subject model of the paper.
// First-order RC cell equivalent circuit driven by a constant current.
model SmokeRC
  parameter Real Q = 3.0 * 3600 "Capacity [As]";
  parameter Real R0 = 0.02 "Series resistance [Ohm]";
  parameter Real R1 = 0.015 "RC resistance [Ohm]";
  parameter Real C1 = 2000 "RC capacitance [F]";
  input Real I(start = 1.5) "Discharge current [A]";
  Real soc(start = 1.0, fixed = true) "State of charge [-]";
  Real v1(start = 0.0, fixed = true) "RC voltage [V]";
  output Real v "Terminal voltage [V]";
equation
  der(soc) = -I / Q;
  der(v1) = -v1 / (R1 * C1) + I / C1;
  v = 3.0 + 1.2 * soc - v1 - R0 * I;
end SmokeRC;
