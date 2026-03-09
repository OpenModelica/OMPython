# -*- coding: utf-8 -*-
"""
Definition of needed tools to execute a compiled (binary) OpenModelica model.
"""

import ast
import dataclasses
import logging
import numbers
import os
import pathlib
import re
import subprocess
from typing import Any, Optional
import warnings

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelExecutionException(Exception):
    """
    Exception which is raised by ModelException* classes.
    """


@dataclasses.dataclass
class ModelExecutionData:
    """
    Data class to store the command line data for running a model executable in the OMC environment.

    All data should be defined for the environment, where OMC is running (local, docker or WSL)

    To use this as a definition of an OMC simulation run, it has to be processed within
    OMCProcess*.self_update(). This defines the attribute cmd_model_executable.
    """
    # cmd_path is the expected working directory
    cmd_path: str
    cmd_model_name: str
    # command prefix data (as list of strings); needed for docker or WSL
    cmd_prefix: list[str]
    # cmd_model_executable is build out of cmd_path and cmd_model_name; this is mainly needed on Windows (add *.exe)
    cmd_model_executable: str
    # command line arguments for the model executable
    cmd_args: list[str]
    # result file with the simulation output
    cmd_result_file: str
    # command timeout
    cmd_timeout: float

    # additional library search path; this is mainly needed if OMCProcessLocal is run on Windows
    cmd_library_path: Optional[str] = None
    # working directory to be used on the *local* system
    cmd_cwd_local: Optional[str] = None

    def get_cmd(self) -> list[str]:
        """
        Get the command line to run the model executable in the environment defined by the OMCProcess definition.
        """

        cmdl = self.cmd_prefix
        cmdl += [self.cmd_model_executable]
        cmdl += self.cmd_args

        return cmdl

    def run(self) -> int:
        """
        Run the model execution defined in this class.
        """

        my_env = os.environ.copy()
        if isinstance(self.cmd_library_path, str):
            my_env["PATH"] = self.cmd_library_path + os.pathsep + my_env["PATH"]

        cmdl = self.get_cmd()

        logger.debug("Run OM command %s in %s", repr(cmdl), self.cmd_path)
        try:
            cmdres = subprocess.run(
                cmdl,
                capture_output=True,
                text=True,
                env=my_env,
                cwd=self.cmd_cwd_local,
                timeout=self.cmd_timeout,
                check=True,
            )
            stdout = cmdres.stdout.strip()
            stderr = cmdres.stderr.strip()
            returncode = cmdres.returncode

            logger.debug("OM output for command %s:\n%s", repr(cmdl), stdout)

            if stderr:
                raise ModelExecutionException(f"Error running model executable {repr(cmdl)}: {stderr}")
        except subprocess.TimeoutExpired as ex:
            raise ModelExecutionException(f"Timeout running model executable {repr(cmdl)}: {ex}") from ex
        except subprocess.CalledProcessError as ex:
            raise ModelExecutionException(f"Error running model executable {repr(cmdl)}: {ex}") from ex

        return returncode


class ModelExecutionCmd:
    """
    All information about a compiled model executable. This should include data about all structured parameters, i.e.
    parameters which need a recompilation of the model. All non-structured parameters can be easily changed without
    the need for recompilation.
    """

    def __init__(
            self,
            runpath: os.PathLike,
            cmd_prefix: list[str],
            cmd_local: bool = False,
            cmd_windows: bool = False,
            timeout: float = 10.0,
            model_name: Optional[str] = None,
    ) -> None:
        if model_name is None:
            raise ModelExecutionException("Missing model name!")

        self._cmd_local = cmd_local
        self._cmd_windows = cmd_windows
        self._cmd_prefix = cmd_prefix
        self._runpath = pathlib.PurePosixPath(runpath)
        self._model_name = model_name
        self._timeout = timeout

        # dictionaries of command line arguments for the model executable
        self._args: dict[str, str | None] = {}
        # 'override' argument needs special handling, as it is a dict on its own saved as dict elements following the
        # structure: 'key' => 'key=value'
        self._arg_override: dict[str, str] = {}

    def arg_set(
            self,
            key: str,
            val: Optional[str | dict[str, Any] | numbers.Number] = None,
    ) -> None:
        """
        Set one argument for the executable model.

        Args:
            key: identifier / argument name to be used for the call of the model executable.
            val: value for the given key; None for no value and for key == 'override' a dictionary can be used which
              indicates variables to override
        """

        def override2str(
                orkey: str,
                orval: str | bool | numbers.Number,
        ) -> str:
            """
            Convert a value for 'override' to a string taking into account differences between Modelica and Python.
            """
            # check oval for any string representations of numbers (or bool) and convert these to Python representations
            if isinstance(orval, str):
                try:
                    val_evaluated = ast.literal_eval(orval)
                    if isinstance(val_evaluated, (numbers.Number, bool)):
                        orval = val_evaluated
                except (ValueError, SyntaxError):
                    pass

            if isinstance(orval, str):
                val_str = orval.strip()
            elif isinstance(orval, bool):
                val_str = 'true' if orval else 'false'
            elif isinstance(orval, numbers.Number):
                val_str = str(orval)
            else:
                raise ModelExecutionException(f"Invalid value for override key {orkey}: {type(orval)}")

            return f"{orkey}={val_str}"

        if not isinstance(key, str):
            raise ModelExecutionException(f"Invalid argument key: {repr(key)} (type: {type(key)})")
        key = key.strip()

        if isinstance(val, dict):
            if key != 'override':
                raise ModelExecutionException("Dictionary input only possible for key 'override'!")

            for okey, oval in val.items():
                if not isinstance(okey, str):
                    raise ModelExecutionException("Invalid key for argument 'override': "
                                                  f"{repr(okey)} (type: {type(okey)})")

                if not isinstance(oval, (str, bool, numbers.Number, type(None))):
                    raise ModelExecutionException(f"Invalid input for 'override'.{repr(okey)}: "
                                                  f"{repr(oval)} (type: {type(oval)})")

                if okey in self._arg_override:
                    if oval is None:
                        logger.info(f"Remove model executable override argument: {repr(self._arg_override[okey])}")
                        del self._arg_override[okey]
                        continue

                    logger.info(f"Update model executable override argument: {repr(okey)} = {repr(oval)} "
                                f"(was: {repr(self._arg_override[okey])})")

                if oval is not None:
                    self._arg_override[okey] = override2str(orkey=okey, orval=oval)

            argval = ','.join(sorted(self._arg_override.values()))
        elif val is None:
            argval = None
        elif isinstance(val, str):
            argval = val.strip()
        elif isinstance(val, numbers.Number):
            argval = str(val)
        else:
            raise ModelExecutionException(f"Invalid argument value for {repr(key)}: {repr(val)} (type: {type(val)})")

        if key in self._args:
            logger.warning(f"Override model executable argument: {repr(key)} = {repr(argval)} "
                           f"(was: {repr(self._args[key])})")
        self._args[key] = argval

    def arg_get(self, key: str) -> Optional[str | dict[str, str | bool | numbers.Number]]:
        """
        Return the value for the given key
        """
        if key in self._args:
            return self._args[key]

        return None

    def args_set(
            self,
            args: dict[str, Optional[str | dict[str, Any] | numbers.Number]],
    ) -> None:
        """
        Define arguments for the model executable.
        """
        for arg in args:
            self.arg_set(key=arg, val=args[arg])

    def get_cmd_args(self) -> list[str]:
        """
        Get a list with the command arguments for the model executable.
        """

        cmdl = []
        for key in sorted(self._args):
            if self._args[key] is None:
                cmdl.append(f"-{key}")
            else:
                cmdl.append(f"-{key}={self._args[key]}")

        return cmdl

    def definition(self) -> ModelExecutionData:
        """
        Define all needed data to run the model executable. The data is stored in an OMCSessionRunData object.
        """
        # ensure that a result filename is provided
        result_file = self.arg_get('r')
        if not isinstance(result_file, str):
            result_file = (self._runpath / f"{self._model_name}.mat").as_posix()

        # as this is the local implementation, pathlib.Path can be used
        cmd_path = self._runpath

        cmd_library_path = None
        if self._cmd_local and self._cmd_windows:
            cmd_library_path = ""

            # set the process environment from the generated .bat file in windows which should have all the dependencies
            # for this pathlib.PurePosixPath() must be converted to a pathlib.Path() object, i.e. WindowsPath
            path_bat = pathlib.Path(cmd_path) / f"{self._model_name}.bat"
            if not path_bat.is_file():
                raise ModelExecutionException("Batch file (*.bat) does not exist " + str(path_bat))

            content = path_bat.read_text(encoding='utf-8')
            for line in content.splitlines():
                match = re.match(pattern=r"^SET PATH=([^%]*)", string=line, flags=re.IGNORECASE)
                if match:
                    cmd_library_path = match.group(1).strip(';')  # Remove any trailing semicolons
            my_env = os.environ.copy()
            my_env["PATH"] = cmd_library_path + os.pathsep + my_env["PATH"]

            cmd_model_executable = cmd_path / f"{self._model_name}.exe"
        else:
            # for Linux the paths to the needed libraries should be included in the executable (using rpath)
            cmd_model_executable = cmd_path / self._model_name

        # define local(!) working directory
        cmd_cwd_local = None
        if self._cmd_local:
            cmd_cwd_local = cmd_path.as_posix()

        omc_run_data = ModelExecutionData(
            cmd_path=cmd_path.as_posix(),
            cmd_model_name=self._model_name,
            cmd_args=self.get_cmd_args(),
            cmd_result_file=result_file,
            cmd_prefix=self._cmd_prefix,
            cmd_library_path=cmd_library_path,
            cmd_model_executable=cmd_model_executable.as_posix(),
            cmd_cwd_local=cmd_cwd_local,
            cmd_timeout=self._timeout,
        )

        return omc_run_data

    @staticmethod
    def parse_simflags(simflags: str) -> dict[str, Optional[str | dict[str, Any] | numbers.Number]]:
        """
        Parse a simflag definition; this is deprecated!

        The return data can be used as input for self.args_set().
        """
        warnings.warn(
            message="The argument 'simflags' is depreciated and will be removed in future versions; "
                    "please use 'simargs' instead",
            category=DeprecationWarning,
            stacklevel=2,
        )

        simargs: dict[str, Optional[str | dict[str, Any] | numbers.Number]] = {}

        args = [s for s in simflags.split(' ') if s]
        for arg in args:
            if arg[0] != '-':
                raise ModelExecutionException(f"Invalid simulation flag: {arg}")
            arg = arg[1:]
            parts = arg.split('=')
            if len(parts) == 1:
                simargs[parts[0]] = None
            elif parts[0] == 'override':
                override = '='.join(parts[1:])

                override_dict = {}
                for item in override.split(','):
                    kv = item.split('=')
                    if not 0 < len(kv) < 3:
                        raise ModelExecutionException(f"Invalid value for '-override': {override}")
                    if kv[0]:
                        try:
                            override_dict[kv[0]] = kv[1]
                        except (KeyError, IndexError) as ex:
                            raise ModelExecutionException(f"Invalid value for '-override': {override}") from ex

                simargs[parts[0]] = override_dict

        return simargs
