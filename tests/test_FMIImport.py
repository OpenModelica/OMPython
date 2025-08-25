import numpy as np
import os
import pytest
import shutil

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


def test_FMIImport(model_firstorder):
    filePath = model_firstorder.as_posix()

    # create model & simulate it
    mod1 = OMPython.ModelicaSystem()
    mod1.model(file=filePath, name="M")
    mod1.simulate()

    # create FMU & check
    fmu = mod1.convertMo2Fmu(fileNamePrefix="M")
    assert os.path.exists(fmu)

    # import FMU & check & simulate
    # TODO: why is '--allowNonStandardModelica=reinitInAlgorithms' needed? any example without this possible?
    mod2 = OMPython.ModelicaSystem(commandLineOptions=['--allowNonStandardModelica=reinitInAlgorithms'])
    mo = mod2.convertFmu2Mo(fmu=fmu)
    assert os.path.exists(mo)

    mod2.simulate()

    # get and verify result
    res1 = mod1.getSolutions(['time', 'x'])
    res2 = mod2.getSolutions(['time', 'x'])

    # check last value for time
    assert res1[0][-1] == res2[0][-1] == 1.0
    # check last value for x
    assert np.isclose(res1[1][-1], 0.3678794515)  # 0.36787945153397683
    assert np.isclose(res2[1][-1], 0.3678794515)  # 0.3678794515707647

    # cleanup
    tmp2 = mod1.getWorkDirectory()
    shutil.rmtree(tmp2, ignore_errors=True)

    tmp2 = mod2.getWorkDirectory()
    shutil.rmtree(tmp2, ignore_errors=True)
