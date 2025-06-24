import OMPython
import pandas as pd
import pathlib
import pytest

@pytest.fixture
def model_doe(tmp_path: pathlib.Path) -> pathlib.Path:
    # see: https://trac.openmodelica.org/OpenModelica/ticket/4052
    mod = tmp_path / "M.mo"
    mod.write_text(f"""
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

    mod_doe = OMPython.ModelicaSystemDoE(
        fileName=model_doe.as_posix(),
        modelName="M",
        parameters=param_doe,
        resultpath=tmpdir,
    )
    mod_doe.prepare()
    df_doe = mod_doe.get_doe()
    assert isinstance(df_doe, pd.DataFrame)
    assert df_doe.shape[0] == 16
    assert df_doe['results available'].sum() == 16

    mod_doe.simulate()
    sol = mod_doe.get_solutions(var_list=['x[1]', 'y[1]'])
    assert len(sol) == 16
