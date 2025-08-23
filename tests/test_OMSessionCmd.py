import OMPython


def test_isPackage():
    omczmq = OMPython.OMCSessionZMQ()
    omccmd = OMPython.OMCSessionCmd(session=omczmq)
    assert not omccmd.isPackage('Modelica')


def test_isPackage2():
    mod = OMPython.ModelicaSystem()
    mod.model(
        name="Modelica.Electrical.Analog.Examples.CauerLowPassAnalog",
        libraries=["Modelica"],
    )
    omccmd = OMPython.OMCSessionCmd(session=mod.session())
    assert omccmd.isPackage('Modelica')


# TODO: add more checks ...
