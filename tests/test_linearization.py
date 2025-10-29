import OMPython
import pytest
import numpy as np


@pytest.fixture
def model_linearTest(tmp_path):
    mod = tmp_path / "M.mo"
    mod.write_text("""
model linearTest
  Real x1(start=1);
  Real x2(start=-2);
  Real x3(start=3);
  Real x4(start=-5);
  parameter Real a=3,b=2,c=5,d=7,e=1,f=4;
equation
  a*x1 =  b*x2 -der(x1);
  der(x2) + c*x3 + d*x1 = x4;
  f*x4 - e*x3 - der(x3) = x1;
  der(x4) = x1 + x2 + der(x3) + x4;
end linearTest;
""")
    return mod


def test_example(model_linearTest):
    mod = OMPython.ModelicaSystem()
    mod.model_definition(
        file=model_linearTest,
        model="linearTest",
    )
    [A, B, C, D] = mod.linearize()
    expected_matrixA = [[-3, 2, 0, 0], [-7, 0, -5, 1], [-1, 0, -1, 4], [0, 1, -1, 5]]
    assert A == expected_matrixA, f"Matrix does not match the expected value. Got: {A}, Expected: {expected_matrixA}"
    assert B == [], f"Matrix does not match the expected value. Got: {B}, Expected: {[]}"
    assert C == [], f"Matrix does not match the expected value. Got: {C}, Expected: {[]}"
    assert D == [], f"Matrix does not match the expected value. Got: {D}, Expected: {[]}"
    assert mod.getLinearInputs() == []
    assert mod.getLinearOutputs() == []
    assert mod.getLinearStates() == ["x1", "x2", "x3", "x4"]


def test_getters(tmp_path):
    model_file = tmp_path / "pendulum.mo"
    model_file.write_text("""
model Pendulum
Real phi(start=Modelica.Constants.pi, fixed=true);
Real omega(start=0, fixed=true);
input Real u1;
input Real u2;
output Real y1;
output Real y2;
parameter Real l = 1.2;
parameter Real g = 9.81;
equation
der(phi) = omega + u2;
der(omega) = -g/l * sin(phi);
y1 = y2 + 0.5*omega;
y2 = phi + u1;
end Pendulum;
""")
    mod = OMPython.ModelicaSystem()
    mod.model_definition(
        file=model_file.as_posix(),
        model="Pendulum",
        libraries=["Modelica"],
    )

    d = mod.getLinearizationOptions()
    assert isinstance(d, dict)
    assert "startTime" in d
    assert "stopTime" in d
    assert mod.getLinearizationOptions(["stopTime", "startTime"]) == [d["stopTime"], d["startTime"]]
    mod.setLinearizationOptions(linearizationOptions={"stopTime": 0.02})
    assert mod.getLinearizationOptions("stopTime") == ["0.02"]

    mod.setInputs(name={"u1": 10, "u2": 0})
    [A, B, C, D] = mod.linearize()
    g = float(mod.getParameters("g")[0])
    l = float(mod.getParameters("l")[0])
    assert mod.getLinearInputs() == ["u1", "u2"]
    assert mod.getLinearStates() == ["omega", "phi"]
    assert mod.getLinearOutputs() == ["y1", "y2"]
    assert np.isclose(A, [[0, g/l], [1, 0]]).all()
    assert np.isclose(B, [[0, 0], [0, 1]]).all()
    assert np.isclose(C, [[0.5, 1], [0, 1]]).all()
    assert np.isclose(D, [[1, 0], [1, 0]]).all()

    # test LinearizationResult
    result = mod.linearize()
    assert result[0] == A
    assert result[1] == B
    assert result[2] == C
    assert result[3] == D
    with pytest.raises(KeyError):
        result[4]

    A2, B2, C2, D2 = result
    assert A2 == A
    assert B2 == B
    assert C2 == C
    assert D2 == D

    assert result.n == 2
    assert result.m == 2
    assert result.p == 2
    assert np.isclose(result.x0, [0, np.pi]).all()
    assert np.isclose(result.u0, [10, 0]).all()
    assert result.stateVars == ["omega", "phi"]
    assert result.inputVars == ["u1", "u2"]
    assert result.outputVars == ["y1", "y2"]
