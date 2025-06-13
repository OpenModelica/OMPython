import OMPython
import pathlib
import os
import pytest


@pytest.fixture
def model_time_str():
    return """model M
  Real r = time;
end M;
"""


@pytest.fixture
def om(tmp_path):
    origDir = pathlib.Path.cwd()
    os.chdir(tmp_path)
    om = OMPython.OMCSessionZMQ()
    os.chdir(origDir)
    return om


def testHelloWorld(om):
    assert om.sendExpression('"HelloWorld!"') == "HelloWorld!"


def test_Translate(om, model_time_str):
    assert om.sendExpression(model_time_str) == ("M",)
    assert om.sendExpression('translateModel(M)') is True


def test_Simulate(om, model_time_str):
    assert om.sendExpression(f'loadString("{model_time_str}")') is True
    om.sendExpression('res:=simulate(M, stopTime=2.0)')
    assert om.sendExpression('res.resultFile')


def test_execute(om):
    assert om.execute('"HelloWorld!"') == '"HelloWorld!"\n'
    assert om.sendExpression('"HelloWorld!"', parsed=False) == '"HelloWorld!"\n'
    assert om.sendExpression('"HelloWorld!"', parsed=True) == 'HelloWorld!'


def test_omcprocessport_execute(om):
    port = om.omc_process.get_port()
    omcp = OMPython.OMCProcessPort(omc_port=port)

    # run 1
    om1 = OMPython.OMCSessionZMQ(omc_process=omcp)
    assert om1.sendExpression('"HelloWorld!"', parsed=False) == '"HelloWorld!"\n'

    # run 2
    om2 = OMPython.OMCSessionZMQ(omc_process=omcp)
    assert om2.sendExpression('"HelloWorld!"', parsed=False) == '"HelloWorld!"\n'

    del om1
    del om2


def test_omcprocessport_simulate(om, model_time_str):
    port = om.omc_process.get_port()
    omcp = OMPython.OMCProcessPort(omc_port=port)

    om = OMPython.OMCSessionZMQ(omc_process=omcp)
    assert om.sendExpression(f'loadString("{model_time_str}")') is True
    om.sendExpression('res:=simulate(M, stopTime=2.0)')
    assert om.sendExpression('res.resultFile') != ""
    del om
