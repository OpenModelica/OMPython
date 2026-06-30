# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import abc
import itertools
import logging
import numbers
import os
import queue
import threading
from typing import Any, cast, Optional, Tuple

from OMPython.model_execution import (
    ModelExecutionData,
)
from OMPython.om_session_abc import (
    OMPathABC,
    OMSessionABC,
)
from OMPython.modelica_system_abc import (
    ModelicaSystemABC,
    ModelicaSystemError,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaDoEABC(metaclass=abc.ABCMeta):
    """
    Base class to run DoEs based on a (Open)Modelica model using ModelicaSystem

    Example
    -------
    ```
    import OMPython
    import pathlib


    def run_doe():
        mypath = pathlib.Path('.')

        model = mypath / "M.mo"
        model.write_text(
            "    model M\n"
            "      parameter Integer p=1;\n"
            "      parameter Integer q=1;\n"
            "      parameter Real a = -1;\n"
            "      parameter Real b = -1;\n"
            "      Real x[p];\n"
            "      Real y[q];\n"
            "    equation\n"
            "      der(x) = a * fill(1.0, p);\n"
            "      der(y) = b * fill(1.0, q);\n"
            "    end M;\n"
        )

        param = {
            # structural
            'p': [1, 2],
            'q': [3, 4],
            # non-structural
            'a': [5, 6],
            'b': [7, 8],
        }

        resdir = mypath / 'DoE'
        resdir.mkdir(exist_ok=True)

        mod = OMPython.ModelicaSystemOMC()
        mod.model(
            model_name="M",
            model_file=model.as_posix(),
        )
        doe_mod = OMPython.ModelicaSystemDoE(
            mod=mod,
            parameters=param,
            resultpath=resdir,
            simargs={"override": {'stopTime': 1.0}},
        )
        doe_mod.prepare()
        doe_def = doe_mod.get_doe_definition()
        doe_mod.simulate()
        doe_sol = doe_mod.get_doe_solutions()

        # ... work with doe_def and doe_sol ...


    if __name__ == "__main__":
        run_doe()
    ```

    """

    # Dictionary keys used in simulation dict (see _sim_dict or get_doe()). These dict keys contain a space and, thus,
    # cannot be used as OM variable identifiers. They are defined here as reference for any evaluation of the data.
    DICT_ID_STRUCTURE: str = 'ID structure'
    DICT_ID_NON_STRUCTURE: str = 'ID non-structure'
    DICT_RESULT_AVAILABLE: str = 'result available'

    def __init__(
            self,
            # ModelicaSystem definition to use
            mod: ModelicaSystemABC,
            # simulation specific input
            # TODO: add more settings (simulation options, input options, ...)
            simargs: Optional[dict[str, Optional[str | dict[str, str] | numbers.Number]]] = None,
            # DoE specific inputs
            resultpath: Optional[str | os.PathLike] = None,
            parameters: Optional[dict[str, list[str] | list[int] | list[float]]] = None,
    ) -> None:
        """
        Initialisation of ModelicaSystemDoE. The parameters are based on: ModelicaSystem.__init__() and
        ModelicaSystem.simulate(). Additionally, the path to store the result files is needed (= resultpath) as well as
        a list of parameters to vary for the Doe (= parameters). All possible combinations are considered.
        """
        if not isinstance(mod, ModelicaSystemABC):
            raise ModelicaSystemError("Missing definition of ModelicaSystem!")

        self._mod = mod
        self._model_name = mod.get_model_name()

        self._simargs = simargs

        if resultpath is None:
            self._resultpath = self.get_session().omcpath_tempdir()
        else:
            self._resultpath = self.get_session().omcpath(resultpath).resolve()
        if not self._resultpath.is_dir():
            raise ModelicaSystemError("Argument resultpath must be set to a valid path within the environment used "
                                      f"for the OpenModelica session: {resultpath}!")

        if isinstance(parameters, dict):
            self._parameters = parameters
        else:
            self._parameters = {}

        self._doe_def: Optional[dict[str, dict[str, Any]]] = None
        self._doe_cmd: Optional[dict[str, ModelExecutionData]] = None

    def get_session(self) -> OMSessionABC:
        """
        Return the OMC session used for this class.
        """
        return self._mod.get_session()

    def get_resultpath(self) -> OMPathABC:
        """
        Get the path there the result data is saved.
        """
        return self._resultpath

    def prepare(self) -> int:
        """
        Prepare the DoE by evaluating the parameters. Each structural parameter requires a new instance of
        ModelicaSystem while the non-structural parameters can just be set on the executable.

        The return value is the number of simulation defined.
        """

        doe_sim = {}
        doe_def = {}

        param_structure = {}
        param_non_structure = {}
        for param_name in self._parameters.keys():
            changeable = self._mod.isParameterChangeable(name=param_name)
            logger.info(f"Parameter {repr(param_name)} is changeable? {changeable}")

            if changeable:
                param_non_structure[param_name] = self._parameters[param_name]
            else:
                param_structure[param_name] = self._parameters[param_name]

        param_structure_combinations = list(itertools.product(*param_structure.values()))
        param_non_structural_combinations = list(itertools.product(*param_non_structure.values()))

        for idx_pc_structure, pc_structure in enumerate(param_structure_combinations):
            sim_param_structure = self._prepare_structure_parameters(
                idx_pc_structure=idx_pc_structure,
                pc_structure=pc_structure,
                param_structure=param_structure,
            )

            for idx_non_structural, pk_non_structural in enumerate(param_non_structural_combinations):
                sim_param_non_structural = {}
                for idx, pk in enumerate(param_non_structure.keys()):
                    sim_param_non_structural[pk] = cast(Any, pk_non_structural[idx])

                resfilename = f"DOE_{idx_pc_structure:09d}_{idx_non_structural:09d}.mat"
                logger.info(f"use result file {repr(resfilename)} "
                            f"for structural parameters: {sim_param_structure} "
                            f"and non-structural parameters: {sim_param_non_structural}")
                resultfile = self._resultpath / resfilename

                df_data = (
                        {
                            self.DICT_ID_STRUCTURE: idx_pc_structure,
                        }
                        | sim_param_structure
                        | {
                            self.DICT_ID_NON_STRUCTURE: idx_non_structural,
                        }
                        | sim_param_non_structural
                        | {
                            self.DICT_RESULT_AVAILABLE: False,
                        }
                )

                self._mod.setParameters(sim_param_non_structural)
                mscmd = self._mod.simulate_cmd(
                    result_file=resultfile,
                )
                if self._simargs is not None:
                    mscmd.args_set(args=self._simargs)
                cmd_definition = mscmd.definition()
                del mscmd

                doe_sim[resfilename] = cmd_definition
                doe_def[resfilename] = df_data

        logger.info(f"Prepared {len(doe_sim)} simulation definitions for the defined DoE.")
        self._doe_cmd = doe_sim
        self._doe_def = doe_def

        return len(doe_sim)

    @abc.abstractmethod
    def _prepare_structure_parameters(
            self,
            idx_pc_structure: int,
            pc_structure: Tuple,
            param_structure: dict[str, list[str] | list[int] | list[float]],
    ) -> dict[str, str | int | float]:
        """
        Handle structural parameters. This should be implemented by the derived class
        """

    def get_doe_definition(self) -> Optional[dict[str, dict[str, Any]]]:
        """
        Get the defined DoE as a dict, where each key is the result filename and the value is a dict of simulation
        settings including structural and non-structural parameters.

        The following code snippet can be used to convert the data to a pandas dataframe:

        ```
        import pandas as pd

        doe_dict = doe_mod.get_doe_definition()
        doe_df = pd.DataFrame.from_dict(data=doe_dict, orient='index')
        ```

        """
        return self._doe_def

    def get_doe_command(self) -> Optional[dict[str, ModelExecutionData]]:
        """
        Get the definitions of simulations commands to run for this DoE.
        """
        return self._doe_cmd

    def simulate(
            self,
            num_workers: int = 3,
    ) -> bool:
        """
        Simulate the DoE using the defined number of workers.

        Returns True if all simulations were done successfully, else False.
        """

        if self._doe_cmd is None or self._doe_def is None:
            raise ModelicaSystemError("DoE preparation missing - call prepare() first!")

        doe_cmd_total = len(self._doe_cmd)
        doe_def_total = len(self._doe_def)

        if doe_cmd_total != doe_def_total:
            raise ModelicaSystemError(f"Mismatch between number simulation commands ({doe_cmd_total}) "
                                      f"and simulation definitions ({doe_def_total}).")

        doe_task_query: queue.Queue = queue.Queue()
        if self._doe_cmd is not None:
            for doe_cmd in self._doe_cmd.values():
                doe_task_query.put(doe_cmd)

        if not isinstance(self._doe_def, dict) or len(self._doe_def) == 0:
            raise ModelicaSystemError("Missing Doe Summary!")

        def worker(worker_id, task_queue):
            while True:
                try:
                    # Get the next task from the queue
                    cmd_definition = task_queue.get(block=False)
                except queue.Empty:
                    logger.info(f"[Worker {worker_id}] No more simulations to run.")
                    break

                if cmd_definition is None:
                    raise ModelicaSystemError("Missing simulation definition!")

                resultfile = cmd_definition.cmd_result_file
                resultpath = self.get_session().omcpath(resultfile)

                logger.info(f"[Worker {worker_id}] Performing task: {resultpath.name}")

                try:
                    returncode = cmd_definition.run()
                    logger.info(f"[Worker {worker_id}] Simulation {resultpath.name} "
                                f"finished with return code: {returncode}")
                except ModelicaSystemError as ex:
                    logger.warning(f"Simulation error for {resultpath.name}: {ex}")

                # Mark the task as done
                task_queue.task_done()

                sim_query_done = doe_cmd_total - doe_task_query.qsize()
                logger.info(f"[Worker {worker_id}] Task completed: {resultpath.name} "
                            f"({doe_cmd_total - sim_query_done}/{doe_cmd_total} = "
                            f"{(doe_cmd_total - sim_query_done) / doe_cmd_total * 100:.2f}% of tasks left)")

        # Create and start worker threads
        logger.info(f"Start simulations for DoE with {doe_cmd_total} simulations "
                    f"using {num_workers} workers ...")
        threads = []
        for i in range(num_workers):
            thread = threading.Thread(target=worker, args=(i, doe_task_query))
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        doe_def_done = 0
        for resultfilename in self._doe_def:
            resultfile = self._resultpath / resultfilename

            # include check for an empty (=> 0B) result file which indicates a crash of the model executable
            # see: https://github.com/OpenModelica/OMPython/issues/261
            # https://github.com/OpenModelica/OpenModelica/issues/13829
            if resultfile.is_file() and resultfile.size() > 0:
                self._doe_def[resultfilename][self.DICT_RESULT_AVAILABLE] = True
                doe_def_done += 1

        logger.info(f"All workers finished ({doe_def_done} of {doe_def_total} simulations with a result file).")

        return doe_def_total == doe_def_done
