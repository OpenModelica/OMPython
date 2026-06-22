import pathlib
import os

import pytest

import OMPython


@pytest.fixture
def model_time_str():
    return """model M
  Real r = time;
end M;
"""


@pytest.fixture
def omcs(tmp_path):
    origDir = pathlib.Path.cwd()
    os.chdir(tmp_path)
    omcs = OMPython.OMCSessionLocal()
    os.chdir(origDir)
    return omcs


def testHelloWorld(omcs):
    assert omcs.sendExpression('"HelloWorld!"') == "HelloWorld!"


def test_Translate(omcs, model_time_str):
    assert omcs.sendExpression(model_time_str) == ("M",)
    assert omcs.sendExpression('translateModel(M)') is True


def test_Simulate(omcs, model_time_str):
    assert omcs.sendExpression(f'loadString("{model_time_str}")') is True
    omcs.sendExpression('res:=simulate(M, stopTime=2.0)')
    assert omcs.sendExpression('res.resultFile')


def test_execute(omcs):
    with pytest.deprecated_call():
        assert omcs.execute('"HelloWorld!"') == '"HelloWorld!"\n'
    assert omcs.sendExpression('"HelloWorld!"', parsed=False) == '"HelloWorld!"\n'
    assert omcs.sendExpression('"HelloWorld!"', parsed=True) == 'HelloWorld!'


def test_omcprocessport_execute(omcs):
    port = omcs.get_port()
    omcs2 = OMPython.OMCSessionPort(omc_port=port)

    # run 1
    assert omcs.sendExpression('"HelloWorld!"', parsed=False) == '"HelloWorld!"\n'

    # run 2
    assert omcs2.sendExpression('"HelloWorld!"', parsed=False) == '"HelloWorld!"\n'

    del omcs2


def test_omcprocessport_simulate(omcs, model_time_str):
    port = omcs.get_port()
    omcs2 = OMPython.OMCSessionPort(omc_port=port)

    assert omcs2.sendExpression(f'loadString("{model_time_str}")') is True
    omcs2.sendExpression('res:=simulate(M, stopTime=2.0)')
    assert omcs2.sendExpression('res.resultFile') != ""

    del omcs2
