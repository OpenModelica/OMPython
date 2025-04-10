import OMPython
import tempfile
import shutil
import unittest
import pathlib
import numpy as np


class Test_Linearization(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix='tmpOMPython.tests'))
        with open(self.tmp / "linearTest.mo", "w") as fout:
            fout.write("""
model linearTest
  Real x1(start=1);
  Real x2(start=-2);
  Real x3(start=3);
  Real x4(start=-5);
  parameter Real a=3,b=2,c=5,d=7,e=1,f=4;
equation
  a*x1 =  b*x2 -der(x1);
  der(x2) + c*x3 + d*x1 = x4;
  f*x4 - e*x3 - der(x3) = x1;
  der(x4) = x1 + x2 + der(x3) + x4;
end linearTest;
""")

    def __del__(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_example(self):
        filePath = (self.tmp / "linearTest.mo").as_posix()
        mod = OMPython.ModelicaSystem(filePath, "linearTest")
        [A, B, C, D] = mod.linearize()
        expected_matrixA = [[-3, 2, 0, 0], [-7, 0, -5, 1], [-1, 0, -1, 4], [0, 1, -1, 5]]
        assert A == expected_matrixA, f"Matrix does not match the expected value. Got: {A}, Expected: {expected_matrixA}"
        assert B == [], f"Matrix does not match the expected value. Got: {B}, Expected: {[]}"
        assert C == [], f"Matrix does not match the expected value. Got: {C}, Expected: {[]}"
        assert D == [], f"Matrix does not match the expected value. Got: {D}, Expected: {[]}"
        assert mod.getLinearInputs() == []
        assert mod.getLinearOutputs() == []
        assert mod.getLinearStates() == ["x1", "x2", "x3", "x4"]

    def test_getters(self):
        model_file = self.tmp / "pendulum.mo"
        model_file.write_text("""
model Pendulum
  Real phi(start=Modelica.Constants.pi, fixed=true);
  Real omega(start=0, fixed=true);
  input Real u1;
  input Real u2;
  output Real y1;
  output Real y2;
  parameter Real l = 1.2;
  parameter Real g = 9.81;
equation
    der(phi) = omega + u2;
    der(omega) = -g/l * sin(phi);
    y1 = y2 + 0.5*omega;
    y2 = phi + u1;
end Pendulum;
""")
        mod = OMPython.ModelicaSystem(model_file.as_posix(), "Pendulum", ["Modelica"], raiseerrors=True)
        mod.setLinearizationOptions("stopTime=0.02")
        mod.setInputs(["u1=0", "u2=0"])
        [A, B, C, D] = mod.linearize()
        g = float(mod.getParameters("g")[0])
        l = float(mod.getParameters("l")[0])
        assert mod.getLinearInputs() == ["u1", "u2"]
        assert mod.getLinearStates() == ["omega", "phi"]
        assert mod.getLinearOutputs() == ["y1", "y2"]
        assert np.isclose(A, [[0, g/l], [1, 0]]).all()
        assert np.isclose(B, [[0, 0], [0, 1]]).all()
        assert np.isclose(C, [[0.5, 1], [0, 1]]).all()
        assert np.isclose(D, [[1, 0], [1, 0]]).all()
