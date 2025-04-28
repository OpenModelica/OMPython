import OMPython
import pathlib
import shutil
import tempfile
import unittest


import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ModelicaSystemCmdTester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ModelicaSystemCmdTester, self).__init__(*args, **kwargs)
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix='tmpOMPython.tests'))
        self.model = self.tmp / "M.mo"
        with open(self.model, "w") as fout:
            fout.write("""model M
  Real x(start = 1, fixed = true);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
                   """)
        self.mod = OMPython.ModelicaSystem(self.model.as_posix(), "M")

    def __del__(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_simflags(self):
        mscmd = OMPython.ModelicaSystemCmd(runpath=self.mod.tempdir, modelname=self.mod.modelName)
        mscmd.args_set(args={"noEventEmit": None, "noRestart": None, "override": {'b': 2}})
        mscmd.args_set(args=mscmd.parse_simflags(simflags="-noEventEmit -noRestart -override=a=1,x=3"))

        logger.info(mscmd.get_cmd())

        assert mscmd.get_cmd() == [mscmd.get_exe().as_posix(), '-noEventEmit', '-noRestart', '-override=b=2,a=1,x=3']


if __name__ == '__main__':
    unittest.main()
