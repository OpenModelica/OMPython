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
def model_firstorder_content():
    return """
model M
  Real x(start = 1, fixed = true);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
"""


@pytest.fixture
def model_firstorder(tmp_path, model_firstorder_content):
    mod = tmp_path / "M.mo"
    mod.write_text(model_firstorder_content)
    return mod


@pytest.fixture
def param():
    x0 = 1
    a = -1
    tau = -1 / a
    stopTime = 5*tau

    return {
        'x0': x0,
        'a': a,
        'stopTime': stopTime,
    }


def test_ModelicaSystemRunner_OMC(model_firstorder, param):
    # create a model using ModelicaSystem
    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_file=model_firstorder,
        model_name="M",
    )

    resultfile_mod = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_mod.mat"
    _run_simulation(mod=mod, resultfile=resultfile_mod, param=param)

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

    resultfile_modr = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_modr.mat"
    _run_simulation(mod=modr, resultfile=resultfile_modr, param=param)

    # cannot check the content as runner does not have the capability to open a result file
    assert resultfile_mod.size() == resultfile_modr.size()

    # check results
    _check_result(mod=mod, resultfile=resultfile_mod, param=param)
    _check_result(mod=mod, resultfile=resultfile_modr, param=param)


def test_ModelicaSystemRunner_local(model_firstorder, param):
    # create a model using ModelicaSystem
    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_file=model_firstorder,
        model_name="M",
    )

    resultfile_mod = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_mod.mat"
    _run_simulation(mod=mod, resultfile=resultfile_mod, param=param)

    # run the model using only the runner class
    omcs = OMPython.OMSessionRunner(
        version=mod.get_session().get_version(),
        ompath_runner=OMPython.OMPathRunnerLocal,
    )
    modr = OMPython.ModelicaSystemRunner(
        session=omcs,
        work_directory=mod.getWorkDirectory(),
    )
    modr.setup(
        model_name="M",
    )

    resultfile_modr = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_modr.mat"
    _run_simulation(mod=modr, resultfile=resultfile_modr, param=param)

    # cannot check the content as runner does not have the capability to open a result file
    assert resultfile_mod.size() == resultfile_modr.size()

    # check results
    _check_result(mod=mod, resultfile=resultfile_mod, param=param)
    _check_result(mod=mod, resultfile=resultfile_modr, param=param)


@skip_on_windows
def test_ModelicaSystemRunner_bash(model_firstorder, param):
    # create a model using ModelicaSystem
    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_file=model_firstorder,
        model_name="M",
    )

    resultfile_mod = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_mod.mat"
    _run_simulation(mod=mod, resultfile=resultfile_mod, param=param)

    # run the model using only the runner class
    omcsr = OMPython.OMSessionRunner(
        version=mod.get_session().get_version(),
        ompath_runner=OMPython.OMPathRunnerBash,
    )
    modr = OMPython.ModelicaSystemRunner(
        session=omcsr,
        work_directory=mod.getWorkDirectory(),
    )
    modr.setup(
        model_name="M",
    )

    resultfile_modr = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_modr.mat"
    _run_simulation(mod=modr, resultfile=resultfile_modr, param=param)

    # cannot check the content as runner does not have the capability to open a result file
    assert resultfile_mod.size() == resultfile_modr.size()

    # check results
    _check_result(mod=mod, resultfile=resultfile_mod, param=param)
    _check_result(mod=mod, resultfile=resultfile_modr, param=param)


@skip_on_windows
@skip_python_older_312
def test_ModelicaSystemRunner_bash_docker(model_firstorder, param):
    omcs = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    assert omcs.get_version() == "OpenModelica 1.25.0"

    # create a model using ModelicaSystem
    mod = OMPython.ModelicaSystemOMC(
        session=omcs,
    )
    mod.model(
        model_file=model_firstorder,
        model_name="M",
    )

    resultfile_mod = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_mod.mat"
    _run_simulation(mod=mod, resultfile=resultfile_mod, param=param)

    # run the model using only the runner class
    omcsr = OMPython.OMSessionRunner(
        version=mod.get_session().get_version(),
        cmd_prefix=omcs.model_execution_prefix(cwd=mod.getWorkDirectory()),
        ompath_runner=OMPython.OMPathRunnerBash,
        model_execution_local=False,
    )
    modr = OMPython.ModelicaSystemRunner(
        session=omcsr,
        work_directory=mod.getWorkDirectory(),
    )
    modr.setup(
        model_name="M",
    )

    resultfile_modr = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_modr.mat"
    _run_simulation(mod=modr, resultfile=resultfile_modr, param=param)

    # cannot check the content as runner does not have the capability to open a result file
    assert resultfile_mod.size() == resultfile_modr.size()

    # check results
    _check_result(mod=mod, resultfile=resultfile_mod, param=param)
    _check_result(mod=mod, resultfile=resultfile_modr, param=param)


@pytest.mark.skip(reason="Not able to run WSL on github")
@skip_python_older_312
def test_ModelicaSystemDoE_WSL(tmp_path, model_doe, param_doe):
    omcs = OMPython.OMCSessionWSL()
    assert omcs.get_version() == "OpenModelica 1.25.0"

    # create a model using ModelicaSystem
    mod = OMPython.ModelicaSystemOMC(
        session=omcs,
    )
    mod.model(
        model_file=model_firstorder,
        model_name="M",
    )

    resultfile_mod = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_mod.mat"
    _run_simulation(mod=mod, resultfile=resultfile_mod, param=param)

    # run the model using only the runner class
    omcsr = OMPython.OMSessionRunner(
        version=mod.get_session().get_version(),
        cmd_prefix=omcs.model_execution_prefix(cwd=mod.getWorkDirectory()),
        ompath_runner=OMPython.OMPathRunnerBash,
        model_execution_local=False,
    )
    modr = OMPython.ModelicaSystemRunner(
        session=omcsr,
        work_directory=mod.getWorkDirectory(),
    )
    modr.setup(
        model_name="M",
    )

    resultfile_modr = mod.getWorkDirectory() / f"{mod.get_model_name()}_res_modr.mat"
    _run_simulation(mod=modr, resultfile=resultfile_modr, param=param)

    # cannot check the content as runner does not have the capability to open a result file
    assert resultfile_mod.size() == resultfile_modr.size()

    # check results
    _check_result(mod=mod, resultfile=resultfile_mod, param=param)
    _check_result(mod=mod, resultfile=resultfile_modr, param=param)


def _run_simulation(mod, resultfile, param):
    simOptions = {"stopTime": param['stopTime'], "stepSize": 0.1, "tolerance": 1e-8}
    mod.setSimulationOptions(**simOptions)
    mod.simulate(resultfile=resultfile)

    assert resultfile.exists()


def _check_result(mod, resultfile, param):
    x = mod.getSolutions(resultfile=resultfile, varList="x")
    t, x2 = mod.getSolutions(resultfile=resultfile, varList=["time", "x"])
    assert (x2 == x).all()
    sol_names = mod.getSolutions(resultfile=resultfile)
    assert isinstance(sol_names, tuple)
    assert "time" in sol_names
    assert "x" in sol_names
    assert "der(x)" in sol_names
    with pytest.raises(OMPython.ModelicaSystemError):
        mod.getSolutions(resultfile=resultfile, varList="thisVariableDoesNotExist")
    assert np.isclose(t[0], 0), "time does not start at 0"
    assert np.isclose(t[-1], param['stopTime']), "time does not end at stopTime"
    x_analytical = param['x0'] * np.exp(param['a']*t)
    assert np.isclose(x, x_analytical, rtol=1e-4).all()
