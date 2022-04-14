/* Linearization */
#include "oc_latch_model.h"
#if defined(__cplusplus)
extern "C" {
#endif
const char *oc_latch_linear_model_frame()
{
  return "model linearized_model \"oc_latch\" \n  parameter Integer n = 0 \"number of states\";\n  parameter Integer m = 0 \"number of inputs\";\n  parameter Integer p = 0 \"number of outputs\";\n"
  "  parameter Real x0[n] = %s;\n"
  "  parameter Real u0[m] = %s;\n"
  "\n"
  "  parameter Real A[n, n] = zeros(n, n);%s\n\n"
  "  parameter Real B[n, m] = zeros(n, m);%s\n\n"
  "  parameter Real C[p, n] = zeros(p, n);%s\n\n"
  "  parameter Real D[p, m] = zeros(p, m);%s\n\n"
  "\n"
  "  Real x[n];\n"
  "  input Real u[m];\n"
  "  output Real y[p];\n"
  "\n"
  "equation\n  der(x) = A * x + B * u;\n  y = C * x + D * u;\nend linearized_model;\n";
}
const char *oc_latch_linear_model_datarecovery_frame()
{
  return "model linearized_model \"oc_latch\" \n parameter Integer n = 0 \"number of states\";\n  parameter Integer m = 0 \"number of inputs\";\n  parameter Integer p = 0 \"number of outputs\";\n  parameter Integer nz = 56 \"data recovery variables\";\n"
  "  parameter Real x0[0] = %s;\n"
  "  parameter Real u0[0] = %s;\n"
  "  parameter Real z0[56] = %s;\n"
  "\n"
  "  parameter Real A[n, n] = zeros(n, n);%s\n\n"
  "  parameter Real B[n, m] = zeros(n, m);%s\n\n"
  "  parameter Real C[p, n] = zeros(p, n);%s\n\n"
  "  parameter Real D[p, m] = zeros(p, m);%s\n\n"
  "  parameter Real Cz[nz, n] = zeros(nz, n);%s\n\n"
  "  parameter Real Dz[nz, m] = zeros(nz, m);%s\n\n"
  "\n"
  "  Real x[n];\n"
  "  input Real u[m];\n"
  "  output Real y[p];\n"
  "  output Real z[nz];\n"
  "\n"
  "  Real 'z_R1.LossPower' = z[1];\n""  Real 'z_R1.R_actual' = z[2];\n""  Real 'z_R1.v' = z[3];\n""  Real 'z_R2.LossPower' = z[4];\n""  Real 'z_R2.R_actual' = z[5];\n""  Real 'z_R2.i' = z[6];\n""  Real 'z_R2.v' = z[7];\n""  Real 'z_capacitor.i' = z[8];\n""  Real 'z_capacitor.n.i' = z[9];\n""  Real 'z_combiTimeTable.timeScaled' = z[10];\n""  Real 'z_combiTimeTable.y[1]' = z[11];\n""  Real 'z_constantVoltage.i' = z[12];\n""  Real 'z_ground.p.v' = z[13];\n""  Real 'z_ground1.p.v' = z[14];\n""  Real 'z_ground2.p.v' = z[15];\n""  Real 'z_ground3.p.i' = z[16];\n""  Real 'z_ground3.p.v' = z[17];\n""  Real 'z_ground4.p.v' = z[18];\n""  Real 'z_ground5.p.i' = z[19];\n""  Real 'z_ground5.p.v' = z[20];\n""  Real 'z_ground6.p.v' = z[21];\n""  Real 'z_opAmp.VMax.i' = z[22];\n""  Real 'z_opAmp.VMin.i' = z[23];\n""  Real 'z_opAmp.absSlope' = z[24];\n""  Real 'z_opAmp.f' = z[25];\n""  Real 'z_opAmp.in_n.i' = z[26];\n""  Real 'z_opAmp.in_p.i' = z[27];\n""  Real 'z_opAmp.vin' = z[28];\n""  Real 'z_opAmp1.VMax.i' = z[29];\n""  Real 'z_opAmp1.VMin.i' = z[30];\n""  Real 'z_opAmp1.absSlope' = z[31];\n""  Real 'z_opAmp1.f' = z[32];\n""  Real 'z_opAmp1.in_n.i' = z[33];\n""  Real 'z_opAmp1.in_p.i' = z[34];\n""  Real 'z_opAmp1.vin' = z[35];\n""  Real 'z_potentialSensor.p.i' = z[36];\n""  Real 'z_potentialSensor.phi' = z[37];\n""  Real 'z_potentialSensor1.p.i' = z[38];\n""  Real 'z_potentialSensor1.phi' = z[39];\n""  Real 'z_resistor.LossPower' = z[40];\n""  Real 'z_resistor.R_actual' = z[41];\n""  Real 'z_resistor.i' = z[42];\n""  Real 'z_resistor.v' = z[43];\n""  Real 'z_resistor1.LossPower' = z[44];\n""  Real 'z_resistor1.R_actual' = z[45];\n""  Real 'z_resistor1.i' = z[46];\n""  Real 'z_resistor1.v' = z[47];\n""  Real 'z_resistor2.LossPower' = z[48];\n""  Real 'z_resistor2.R_actual' = z[49];\n""  Real 'z_resistor2.v' = z[50];\n""  Real 'z_resistor3.LossPower' = z[51];\n""  Real 'z_resistor3.R_actual' = z[52];\n""  Real 'z_resistor3.i' = z[53];\n""  Real 'z_resistor3.v' = z[54];\n""  Real 'z_signalVoltage.i' = z[55];\n""  Real 'z_signalVoltage.n.i' = z[56];\n"
  "equation\n  der(x) = A * x + B * u;\n  y = C * x + D * u;\n  z = Cz * x + Dz * u;\nend linearized_model;\n";
}
#if defined(__cplusplus)
}
#endif

