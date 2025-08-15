import OMPython
import numpy as np


def test_optimization_example(tmp_path):
    model_file = tmp_path / "BangBang2021.mo"
    model_file.write_text("""
model BangBang2021 "Model to verify that optimization gives bang-bang optimal control"
parameter Real m = 1;
parameter Real p = 1 "needed for final constraints";

Real a;
Real v(start = 0, fixed = true);
Real pos(start = 0, fixed = true);
Real pow(min = -30, max = 30) = f * v annotation(isConstraint = true);

input Real f(min = -10, max = 10);

Real costPos(nominal = 1) = -pos "minimize -pos(tf)" annotation(isMayer=true);

Real conSpeed(min = 0, max = 0) = p * v " 0<= p*v(tf) <=0" annotation(isFinalConstraint = true);

equation

der(pos) = v;
der(v) = a;
f = m * a;

annotation(experiment(StartTime = 0, StopTime = 1, Tolerance = 1e-07, Interval = 0.01),
__OpenModelica_simulationFlags(s="optimization", optimizerNP="1"),
__OpenModelica_commandLineOptions="+g=Optimica");

end BangBang2021;
""")

    mod = OMPython.ModelicaSystem(fileName=model_file.as_posix(), modelName="BangBang2021")

    mod.setOptimizationOptions(optimizationOptions={"numberOfIntervals": 16,
                                                    "stopTime": 1,
                                                    "stepSize": 0.001,
                                                    "tolerance": 1e-8})

    # test the getter
    assert mod.getOptimizationOptions()["stopTime"] == "1"
    assert mod.getOptimizationOptions("stopTime") == ["1"]
    assert mod.getOptimizationOptions(["tolerance", "stopTime"]) == ["1e-08", "1"]

    r = mod.optimize()
    # it is necessary to specify resultfile, otherwise it wouldn't find it.
    time, f, v = mod.getSolutions(["time", "f", "v"], resultfile=r["resultFile"])
    assert np.isclose(f[0], 10)
    assert np.isclose(f[-1], -10)

    def f_fcn(time, v):
        if time < 0.3:
            return 10
        if time <= 0.5:
            return 30 / v
        if time < 0.7:
            return -30 / v
        return -10
    f_expected = [f_fcn(t, v) for t, v in zip(time, v)]

    # The sharp edge at time=0.5 probably won't match, let's leave that out.
    matches = np.isclose(f, f_expected, 1e-3)
    assert matches[:498].all()
    assert matches[502:].all()
