import OMPython
import unittest
import tempfile, shutil, os

class ModelicaSystemTester(unittest.TestCase):
  def __init__(self, *args, **kwargs):
    super(ModelicaSystemTester, self).__init__(*args, **kwargs)
    self.tmp = tempfile.mkdtemp(prefix='tmpOMPython.tests')
    with open("%s/M.mo" % self.tmp, "w") as fout:
      fout.write("""model M
  Real x(start = 1);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
""")
  def __del__(self):
    shutil.rmtree(self.tmp, ignore_errors=True)

  def testModelicaSystemLoop(self):
    def worker():
      filePath = os.path.join(self.tmp,"M.mo").replace("\\", "/")
      m = OMPython.ModelicaSystem(filePath, "M")
      m.simulate()
      m.convertMo2Fmu(fmuType="me")
    for _ in range(10):
      worker()

if __name__ == '__main__':
    unittest.main()
