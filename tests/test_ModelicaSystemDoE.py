import pathlib
import sys

import numpy as np
import pytest

import OMPython

skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="OpenModelica Docker image is Linux-only; skipping on Windows.",
)

skip_python_older_312 = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="OMCPath(non-local) only working for Python >= 3.12.",
)


@pytest.fixture
def model_doe(tmp_path: pathlib.Path) -> pathlib.Path:
    # see: https://trac.openmodelica.org/OpenModelica/ticket/4052
    mod = tmp_path / "M.mo"
    # TODO: update for bool and string parameters; check if these can be used in DoE
    mod.write_text("""
model M
  parameter Integer p=1;
  parameter Integer q=1;
  parameter Real a = -1;
  parameter Real b = -1;
  Real x[p];
  Real y[q];
equation
  der(x) = a * fill(1.0, p);
  der(y) = b * fill(1.0, q);
end M;
""")
    return mod


@pytest.fixture
def param_doe() -> dict[str, list]:
    param = {
        # structural
        'p': [1, 2],
        'q': [3, 4],
        # simple
        'a': [5, 6],
        'b': [7, 8],
    }
    return param


def test_ModelicaSystemDoE_local(tmp_path, model_doe, param_doe):
    tmpdir = tmp_path / 'DoE'
    tmpdir.mkdir(exist_ok=True)

    doe_mod = OMPython.ModelicaSystemDoE(
        model_file=model_doe,
        model_name="M",
        parameters=param_doe,
        resultpath=tmpdir,
        simargs={"override": {'stopTime': 1.0}},
    )

    _run_ModelicaSystemDoe(doe_mod=doe_mod)


@skip_on_windows
@skip_python_older_312
def test_ModelicaSystemDoE_docker(tmp_path, model_doe, param_doe):
    omcs = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    assert omcs.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    doe_mod = OMPython.ModelicaSystemDoE(
        model_file=model_doe,
        model_name="M",
        parameters=param_doe,
        session=omcs,
        simargs={"override": {'stopTime': 1.0}},
    )

    _run_ModelicaSystemDoe(doe_mod=doe_mod)


@pytest.mark.skip(reason="Not able to run WSL on github")
@skip_python_older_312
def test_ModelicaSystemDoE_WSL(tmp_path, model_doe, param_doe):
    tmpdir = tmp_path / 'DoE'
    tmpdir.mkdir(exist_ok=True)

    doe_mod = OMPython.ModelicaSystemDoE(
        model_file=model_doe,
        model_name="M",
        parameters=param_doe,
        resultpath=tmpdir,
        simargs={"override": {'stopTime': 1.0}},
    )

    _run_ModelicaSystemDoe(doe_mod=doe_mod)


def _run_ModelicaSystemDoe(doe_mod):
    doe_count = doe_mod.prepare()
    assert doe_count == 16

    doe_def = doe_mod.get_doe_definition()
    assert isinstance(doe_def, dict)
    assert len(doe_def.keys()) == doe_count

    doe_cmd = doe_mod.get_doe_command()
    assert isinstance(doe_cmd, dict)
    assert len(doe_cmd.keys()) == doe_count

    doe_status = doe_mod.simulate()
    assert doe_status is True

    doe_sol = doe_mod.get_doe_solutions()
    assert isinstance(doe_sol, dict)
    assert len(doe_sol.keys()) == doe_count

    assert sorted(doe_def.keys()) == sorted(doe_cmd.keys())
    assert sorted(doe_cmd.keys()) == sorted(doe_sol.keys())

    for resultfilename in doe_def:
        row = doe_def[resultfilename]

        assert resultfilename in doe_sol
        sol = doe_sol[resultfilename]

        var_dict = {
            # simple / non-structural parameters
            'a': float(row['a']),
            'b': float(row['b']),
            # structural parameters
            'p': float(row['p']),
            'q': float(row['q']),
            # variables using the structural parameters
            f"x[{row['p']}]": float(row['a']),
            f"y[{row['p']}]": float(row['b']),
        }

        for var in var_dict:
            assert var in sol['data']
            assert np.isclose(sol['data'][var][-1], var_dict[var])
