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
