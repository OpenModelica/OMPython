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


@pytest.fixture
def mscmd_firstorder(model_firstorder):
    mod = OMPython.ModelicaSystem(fileName=model_firstorder.as_posix(), modelName="M")
    mscmd = OMPython.ModelicaSystemCmd(runpath=mod.getWorkDirectory(), modelname=mod._model_name)
    return mscmd


def test_simflags(mscmd_firstorder):
    mscmd = mscmd_firstorder

    mscmd.args_set({
        "noEventEmit": None,
        "override": {'b': 2}
    })
    with pytest.deprecated_call():
        mscmd.args_set(args=mscmd.parse_simflags(simflags="-noEventEmit -noRestart -override=a=1,x=3"))

    assert mscmd.get_cmd() == [
        mscmd.get_exe().as_posix(),
        '-noEventEmit',
        '-override=b=2,a=1,x=3',
        '-noRestart',
    ]
