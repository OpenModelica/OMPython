import OMPython
import pytest


@pytest.fixture
def model_firstorder(tmp_path):
    mod = tmp_path / "M.mo"
    mod.write_text("""model M
  Real x(start = 1, fixed = true);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
""")
    return mod


def test_simflags(model_firstorder):
    mod = OMPython.ModelicaSystem(model_firstorder.as_posix(), "M")
    mscmd = OMPython.ModelicaSystemCmd(runpath=mod.tempdir, modelname=mod.modelName)
    mscmd.args_set({
        "noEventEmit": None,
        "noRestart": None,
        "override": {'b': 2}
    })
    mscmd.args_set(args=mscmd.parse_simflags(simflags="-noEventEmit -noRestart -override=a=1,x=3"))

    assert mscmd.get_cmd() == [
        mscmd.get_exe().as_posix(),
        '-noEventEmit', '-noRestart',
        '-override=b=2,a=1,x=3'
    ]
