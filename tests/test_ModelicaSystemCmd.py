import pytest

import OMPython


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
    mod = OMPython.ModelicaSystem()
    mod.model(
        model_file=model_firstorder,
        model_name="M",
    )
    mscmd = OMPython.ModelicaSystemCmd(
        session=mod.get_session(),
        runpath=mod.getWorkDirectory(),
        modelname=mod._model_name,
    )
    return mscmd


def test_simflags(mscmd_firstorder):
    mscmd = mscmd_firstorder

    mscmd.args_set({
        "noEventEmit": None,
        "override": {'b': 2, 'a': 4},
    })

    assert mscmd.get_cmd_args() == [
        '-noEventEmit',
        '-override=a=4,b=2',
    ]

    mscmd.args_set({
        "override": {'b': None},
    })

    assert mscmd.get_cmd_args() == [
        '-noEventEmit',
        '-override=a=4',
    ]
