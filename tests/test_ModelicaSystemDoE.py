import numpy as np
import OMPython
import pathlib
import pytest


@pytest.fixture
def model_doe(tmp_path: pathlib.Path) -> pathlib.Path:
    # see: https://trac.openmodelica.org/OpenModelica/ticket/4052
    mod = tmp_path / "M.mo"
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


def test_ModelicaSystemDoE(tmp_path, model_doe, param_doe):
    tmpdir = tmp_path / 'DoE'
    tmpdir.mkdir(exist_ok=True)

    doe_mod = OMPython.ModelicaSystemDoE(
        fileName=model_doe.as_posix(),
        modelName="M",
        parameters=param_doe,
        resultpath=tmpdir,
        simargs={"override": {'stopTime': 1.0}},
    )
    doe_count = doe_mod.prepare()
    assert doe_count == 16

    doe_dict = doe_mod.get_doe()
    assert isinstance(doe_dict, dict)
    assert len(doe_dict.keys()) == 16

    doe_status = doe_mod.simulate()
    assert doe_status is True

    doe_sol = doe_mod.get_solutions()

    for resultfilename in doe_dict:
        row = doe_dict[resultfilename]

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
