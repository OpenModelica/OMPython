import OMPython
import unittest


class OMCSessionCmdTester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OMCSessionCmdTester, self).__init__(*args, **kwargs)

    def test_isPackage(self):
        omczmq = OMPython.OMCSessionZMQ()
        omccmd = OMPython.OMCSessionCmd(session=omczmq)
        assert not omccmd.isPackage('Modelica')

    def test_isPackage2(self):
        mod = OMPython.ModelicaSystem(modelName="Modelica.Electrical.Analog.Examples.CauerLowPassAnalog",
                                      lmodel=["Modelica"])
        omccmd = OMPython.OMCSessionCmd(session=mod.getconn)
        assert omccmd.isPackage('Modelica')

    # TODO: add more checks ...


if __name__ == '__main__':
    unittest.main()
