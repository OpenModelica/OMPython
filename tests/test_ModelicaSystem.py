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
      origDir = os.getcwd()
      os.chdir(self.tmp)
      m = OMPython.ModelicaSystem("M.mo", "M")
      m.simulate()
      m.convertMo2Fmu(fmuType="me")
      os.chdir(origDir)
    for _ in range(10):
      worker()

if __name__ == '__main__':
    unittest.main()
