import OMPython
import tempfile
import shutil
import unittest
import pathlib


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
        print(filePath)
        mod = OMPython.ModelicaSystem(filePath, "linearTest")
        [A, B, C, D] = mod.linearize()
        expected_matrixA = [[-3, 2, 0, 0], [-7, 0, -5, 1], [-1, 0, -1, 4], [0, 1, -1, 5]]
        assert A == expected_matrixA, f"Matrix does not match the expected value. Got: {A}, Expected: {expected_matrixA}"
        assert B == [], f"Matrix does not match the expected value. Got: {B}, Expected: {[]}"
        assert C == [], f"Matrix does not match the expected value. Got: {C}, Expected: {[]}"
        assert D == [], f"Matrix does not match the expected value. Got: {D}, Expected: {[]}"
