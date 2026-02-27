import OMPython


def test_isPackage():
    omczmq = OMPython.OMCSessionZMQ()
    omccmd = OMPython.OMCSessionCmd(session=omczmq)
    assert not omccmd.isPackage('Modelica')


def test_isPackage2():
    mod = OMPython.ModelicaSystem(modelName="Modelica.Electrical.Analog.Examples.CauerLowPassAnalog",
                                  lmodel=["Modelica"])
    omccmd = OMPython.OMCSessionCmd(session=mod._getconn)
    assert omccmd.isPackage('Modelica')


# TODO: add more checks ...
