model RLC_series "A resistor-inductor-capacitor circuit in series with a voltage source"
  type Current=Real(unit="A");
  type Voltage=Real(unit="V");
  type Capacitance=Real(unit="F");
  type Inductance=Real(unit="H");
  type Resistance=Real(unit="Ohm");
  parameter Voltage V_source = 1;
  parameter Resistance R = 1;
  parameter Inductance L = 1;
  parameter Capacitance C = 1;
  Current i;
  Voltage v_C;
  Voltage v_L;
  Voltage v_R;
equation
  V_source = v_C + v_L + v_R;
  C*der(v_C) = i;
  L*der(i) = v_L;
  R*i = v_R;
end RLC_series;
