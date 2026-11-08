import pytest

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


def test_error_message_file():
    # omc names the file field of a message filename or fileName (OpenModelica issue 17891)
    omcs = OMPython.OMCSessionLocal()
    with pytest.raises(OMPython.OMSessionException, match=r"\[bad\.mo:"):
        omcs.sendExpression('loadString("model M Real x = ; end M;", "bad.mo")')
