import OMPython


def test_isPackage():
    omcs = OMPython.OMCSessionLocal()
    omccmd = OMPython.OMCSessionCmd(session=omcs)
    assert not omccmd.isPackage('Modelica')


def test_isPackage2():
    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_name="Modelica.Electrical.Analog.Examples.CauerLowPassAnalog",
        libraries=["Modelica"],
    )
    omccmd = OMPython.OMCSessionCmd(session=mod.get_session())
    assert omccmd.isPackage('Modelica')


# TODO: add more checks ...
