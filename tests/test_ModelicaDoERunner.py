import pathlib
import sys

import numpy as np
import pytest

import OMPython

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
        # simple
        'a': [5, 6],
        'b': [7, 8],
    }
    return param


def test_ModelicaDoERunner_ModelicaSystemOMC(tmp_path, model_doe, param_doe):
    tmpdir = tmp_path / 'DoE'
    tmpdir.mkdir(exist_ok=True)

    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_file=model_doe,
        model_name="M",
    )

    resultfile_mod = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_mod.mat"
    _run_simulation(mod=mod, resultfile=resultfile_mod, param=param_doe)

    doe_mod = OMPython.ModelicaDoERunner(
        mod=mod,
        parameters=param_doe,
        resultpath=tmpdir,
    )

    _run_ModelicaDoERunner(doe_mod=doe_mod)

    _check_runner_result(mod=mod, doe_mod=doe_mod)


def test_ModelicaDoERunner_ModelicaSystemRunner(tmp_path, model_doe, param_doe):
    tmpdir = tmp_path / 'DoE'
    tmpdir.mkdir(exist_ok=True)

    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_file=model_doe,
        model_name="M",
    )

    resultfile_mod = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_mod.mat"
    _run_simulation(mod=mod, resultfile=resultfile_mod, param=param_doe)

    # run the model using only the runner class
    omcs = OMPython.OMSessionRunner(
        version=mod.get_session().get_version(),
    )
    modr = OMPython.ModelicaSystemRunner(
        session=omcs,
        work_directory=mod.getWorkDirectory(),
    )
    modr.setup(
        model_name="M",
    )
    doe_mod = OMPython.ModelicaDoERunner(
        mod=modr,
        parameters=param_doe,
        resultpath=tmpdir,
    )

    _run_ModelicaDoERunner(doe_mod=doe_mod)

    _check_runner_result(mod=mod, doe_mod=doe_mod)


def _run_simulation(mod, resultfile, param):
    simOptions = {"stopTime": 1.0, "stepSize": 0.1, "tolerance": 1e-8}
    mod.setSimulationOptions(**simOptions)
    mod.simulate(resultfile=resultfile)

    assert resultfile.exists()


def _run_ModelicaDoERunner(doe_mod):
    doe_count = doe_mod.prepare()
    assert doe_count == 4

    doe_def = doe_mod.get_doe_definition()
    assert isinstance(doe_def, dict)
    assert len(doe_def.keys()) == doe_count

    doe_cmd = doe_mod.get_doe_command()
    assert isinstance(doe_cmd, dict)
    assert len(doe_cmd.keys()) == doe_count

    doe_status = doe_mod.simulate()
    assert doe_status is True


def _check_runner_result(mod, doe_mod):
    doe_cmd = doe_mod.get_doe_command()
    doe_def = doe_mod.get_doe_definition()

    doe_sol = OMPython.doe_get_solutions(
        msomc=mod,
        resultpath=doe_mod.get_resultpath(),
        doe_def=doe_def,
    )
    assert isinstance(doe_sol, dict)
    assert len(doe_sol.keys()) == len(doe_cmd.keys())

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
        }

        for key, val in var_dict.items():
            assert key in sol['data']
            assert np.isclose(sol['data'][key][-1], val)
