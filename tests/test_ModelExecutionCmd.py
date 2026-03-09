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
    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_file=model_firstorder,
        model_name="M",
    )

    mscmd = OMPython.ModelExecutionCmd(
        runpath=mod.getWorkDirectory(),
        cmd_local=mod.get_session().model_execution_local,
        cmd_windows=mod.get_session().model_execution_windows,
        cmd_prefix=mod.get_session().model_execution_prefix(cwd=mod.getWorkDirectory()),
        model_name=mod.get_model_name(),
    )

    return mscmd


def test_simflags(mscmd_firstorder):
    mscmd = mscmd_firstorder

    mscmd.args_set(args={
        "override": {
            'b': 2,
            'a': 4,
        },
        "noRestart": None,
        "noEventEmit": None,
    })

    assert mscmd.get_cmd_args() == [
        '-noEventEmit',
        '-noRestart',
        '-override=a=4,b=2',
    ]

    mscmd.args_set({
        "override": {'b': None},
    })

    assert mscmd.get_cmd_args() == [
        '-noEventEmit',
        '-noRestart',
        '-override=a=4',
    ]
