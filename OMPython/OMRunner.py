import os
import platform
import subprocess
import shlex
from typing import Optional, Any
import xml.etree.ElementTree as ET
import logging
import numbers
# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemError(Exception):
    """
    Exception used in ModelicaSystem and ModelicaSystemCmd classes.
    """

class ModelicaSystemRunner(object):
    def __init__(
            self,
            runpath: str,
            modelname: Optional[str] = None,
            variableFilter: Optional[list] = None,
    ) -> None:
        if modelname is None:
            raise ModelicaSystemError("Missing model name!")
        self.runpath = os.path.abspath(runpath)
        self._quantities: list[dict[str, Any]] = []
        self._params: dict[str, str] = {}  # even numerical values are stored as str
        self._inputs: dict[str, list[tuple[float, float]]] = {}
        # self.quantitiesList=[]
        # self.paramlist={}
        # self.inputlist={}
        # self.outputlist={}
        # self.continuouslist={}
        # _outputs values are str before simulate(), but they can be
        # np.float64 after simulate().
        self._outputs: dict[str, Any] = {}
        # same for _continuous
        self._continuous: dict[str, Any] = {}
        self._simulate_options: dict[str, str] = {}
        self._override_variables: dict[str, str] = {}
        self._simulate_options_override: dict[str, str] = {}
        # self.simulateOptions={}
        # self.overridevariables={}
        # self.simoptionsoverride={}
        # self.optimizeOptions={'startTime':0.0, 'stopTime': 1.0, 'numberOfIntervals':500, 'stepSize':0.002, 'tolerance':1e-8}
        # self.linearquantitiesList = []  # linearization  quantity list
        self._linearization_options: dict[str, str | float] = {
            'startTime': 0.0,
            'stopTime': 1.0,
            'stepSize': 0.002,
            'tolerance': 1e-8,
        }
        self._optimization_options = self._linearization_options | {
            'numberOfIntervals': 500,
        }
        print(self.runpath)
        exefile = os.path.join(self.runpath, modelname)
        if not os.path.isfile(exefile):
            raise ModelicaSystemError("Executable model file not found in {0}".format(exefile))
        self.xmlFileName = modelname + "_init.xml"
        self.xmlFile = os.path.join(self.runpath, self.xmlFileName)
        self.modelName = modelname  # Model class name
        self.inputFlag = False  # for model with input quantity
        self.simulationFlag = False  # if the model is simulated?
        self.outputFlag = False
        self.csvFile = ''  # for storing inputs condition
        self.resultfile="" # for storing result file
        self.variableFilter = variableFilter
        self._xmlparse(xml_file=self.xmlFile)
        self._variable_filter: Optional[str] = None
        print("Init done")

    def _xmlparse(self, xml_file: str):
        if not os.path.isfile(xml_file):
            raise ModelicaSystemError(f"XML file not generated: {xml_file}")

        #xml_content = xml_file.read_text()
        #tree = ET.ElementTree(ET.fromstring(xml_content))
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for attr in root.iter('DefaultExperiment'):
            for key in ("startTime", "stopTime", "stepSize", "tolerance",
                        "solver", "outputFormat"):
                self._simulate_options[key] = str(attr.get(key))

        for sv in root.iter('ScalarVariable'):
            translations = {
                "alias": "alias",
                "aliasvariable": "aliasVariable",
                "causality": "causality",
                "changeable": "isValueChangeable",
                "description": "description",
                "name": "name",
                "variability": "variability",
            }

            scalar: dict[str, Any] = {}
            for key_dst, key_src in translations.items():
                val = sv.get(key_src)
                scalar[key_dst] = None if val is None else str(val)

            ch = list(sv)
            for att in ch:
                scalar["start"] = att.get('start')
                scalar["min"] = att.get('min')
                scalar["max"] = att.get('max')
                scalar["unit"] = att.get('unit')

            # save parameters in the corresponding class variables
            if scalar["variability"] == "parameter":
                if scalar["name"] in self._override_variables:
                    self._params[scalar["name"]] = self._override_variables[scalar["name"]]
                else:
                    self._params[scalar["name"]] = scalar["start"]
            if scalar["variability"] == "continuous":
                self._continuous[scalar["name"]] = scalar["start"]
            if scalar["causality"] == "input":
                self._inputs[scalar["name"]] = scalar["start"]
            if scalar["causality"] == "output":
                self._outputs[scalar["name"]] = scalar["start"]

            self._quantities.append(scalar)

    def getQuantities(self, names: Optional[str | list[str]] = None) -> list[dict]:
        """
        This method returns list of dictionaries. It displays details of
        quantities such as name, value, changeable, and description.

        Examples:
            >>> mod.getQuantities()
            [
              {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'local',
                'changeable': 'true',
                'description': None,
                'max': None,
                'min': None,
                'name': 'x',
                'start': '1.0',
                'unit': None,
                'variability': 'continuous',
              },
              {
                'name': 'der(x)',
                # ...
              },
              # ...
            ]

            >>> getQuantities("y")
            [{
              'name': 'y', # ...
            }]

            >>> getQuantities(["y","x"])
            [
              {
                'name': 'y', # ...
              },
              {
                'name': 'x', # ...
              }
            ]
        """
        if names is None:
            return self._quantities

        if isinstance(names, str):
            r = [x for x in self._quantities if x["name"] == names]
            if r == []:
                raise KeyError(names)
            return r

        if isinstance(names, list):
            return [x for y in names for x in self._quantities if x["name"] == y]

        raise ModelicaSystemError("Unhandled input for getQuantities()")

    def getParameters(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str] | list[str]:
        """Get parameter values.

        Args:
            names: Either None (default), a string with the parameter name,
              or a list of parameter name strings.
        Returns:
            If `names` is None, a dict in the format
            {parameter_name: parameter_value} is returned.
            If `names` is a string, a single element list is returned.
            If `names` is a list, a list with one value for each parameter name
            in names is returned.
            In all cases, parameter values are returned as strings.

        Examples:
            >>> mod.getParameters()
            {'Name1': '1.23', 'Name2': '4.56'}
            >>> mod.getParameters("Name1")
            ['1.23']
            >>> mod.getParameters(["Name1","Name2"])
            ['1.23', '4.56']
        """
        if names is None:
            return self._params
        if isinstance(names, str):
            return [self._params[names]]
        if isinstance(names, list):
            return [self._params[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getParameters()")

    def getInputs(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, list[tuple[float, float]]] | list[list[tuple[float, float]]]:
        """Get values of input signals.

        Args:
            names: Either None (default), a string with the input name,
              or a list of input name strings.
        Returns:
            If `names` is None, a dict in the format
            {input_name: input_value} is returned.
            If `names` is a string, a single element list [input_value] is
            returned.
            If `names` is a list, a list with one value for each input name
            in names is returned: [input1_values, input2_values, ...].
            In all cases, input values are returned as a list of tuples,
            where the first element in the tuple is the time and the second
            element is the input value.

        Examples:
            >>> mod.getInputs()
            {'Name1': [(0.0, 0.0), (1.0, 1.0)], 'Name2': None}
            >>> mod.getInputs("Name1")
            [[(0.0, 0.0), (1.0, 1.0)]]
            >>> mod.getInputs(["Name1","Name2"])
            [[(0.0, 0.0), (1.0, 1.0)], None]
        """
        if names is None:
            return self._inputs
        if isinstance(names, str):
            return [self._inputs[names]]
        if isinstance(names, list):
            return [self._inputs[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getInputs()")
    
    def getOutputs(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str | numbers.Real] | list[str | numbers.Real]:
        """Get values of output signals.

        If called before simulate(), the initial values are returned as
        strings. If called after simulate(), the final values (at stopTime)
        are returned as numpy.float64.

        Args:
            names: Either None (default), a string with the output name,
              or a list of output name strings.
        Returns:
            If `names` is None, a dict in the format
            {output_name: output_value} is returned.
            If `names` is a string, a single element list [output_value] is
            returned.
            If `names` is a list, a list with one value for each output name
            in names is returned: [output1_value, output2_value, ...].

        Examples:
            Before simulate():
            >>> mod.getOutputs()
            {'out1': '-0.4', 'out2': '1.2'}
            >>> mod.getOutputs("out1")
            ['-0.4']
            >>> mod.getOutputs(["out1","out2"])
            ['-0.4', '1.2']

            After simulate():
            >>> mod.getOutputs()
            {'out1': np.float64(-0.1234), 'out2': np.float64(2.1)}
            >>> mod.getOutputs("out1")
            [np.float64(-0.1234)]
            >>> mod.getOutputs(["out1","out2"])
            [np.float64(-0.1234), np.float64(2.1)]
        """
        # not self.simulationFlag:
        if names is None:
            return self.outputlist
        elif isinstance(names, str):
            return [self.outputlist.get(names, "NotExist")]
        else:
            return [self.outputlist.get(x, "NotExist") for x in names]

    def getSimulationOptions(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str] | list[str]:
        """Get simulation options such as stopTime and tolerance.

        Args:
            names: Either None (default), a string with the simulation option
              name, or a list of option name strings.

        Returns:
            If `names` is None, a dict in the format
            {option_name: option_value} is returned.
            If `names` is a string, a single element list [option_value] is
            returned.
            If `names` is a list, a list with one value for each option name
            in names is returned: [option1_value, option2_value, ...].
            Option values are always returned as strings.

        Examples:
            >>> mod.getSimulationOptions()
            {'startTime': '0', 'stopTime': '1.234',
             'stepSize': '0.002', 'tolerance': '1.1e-08', 'solver': 'dassl', 'outputFormat': 'mat'}
            >>> mod.getSimulationOptions("stopTime")
            ['1.234']
            >>> mod.getSimulationOptions(["tolerance", "stopTime"])
            ['1.1e-08', '1.234']
        """
        if names is None:
            return self._simulate_options
        if isinstance(names, str):
            return [self._simulate_options[names]]
        if isinstance(names, list):
            return [self._simulate_options[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getSimulationOptions()")

    def getOptimizationOptions(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str | float] | list[str | float]:
        """Get simulation options used for optimization.

        Args:
            names: Either None (default), a string with the optimization option
              name, or a list of option name strings.

        Returns:
            If `names` is None, a dict in the format
            {option_name: option_value} is returned.
            If `names` is a string, a single element list [option_value] is
            returned.
            If `names` is a list, a list with one value for each option name
            in names is returned: [option1_value, option2_value, ...].
            Some option values are returned as float when first initialized,
            but always as strings after setOptimizationOptions is used to
            change them.

        Examples:
            >>> mod.getOptimizationOptions()
            {'startTime': 0.0, 'stopTime': 1.0, 'numberOfIntervals': 500, 'stepSize': 0.002, 'tolerance': 1e-08}
            >>> mod.getOptimizationOptions("stopTime")
            [1.0]
            >>> mod.getOptimizationOptions(["tolerance", "stopTime"])
            [1e-08, 1.0]
        """
        if names is None:
            return self._optimization_options
        if isinstance(names, str):
            return [self._optimization_options[names]]
        if isinstance(names, list):
            return [self._optimization_options[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getOptimizationOptions()")
    

    def simulate(self,resultfile=None,simflags=None,overrideaux=None):  # 11
        """
        This method simulates model according to the simulation options.

        Parameters
        ----------
        resultfile : str or None
            Output file name

        simflags : str or None
            Other simulation options not '-override' parameters

        overrideaux : str or None
            Specify 'outputFormat' and 'variableFilter

        usage
        -----
        >>> simulate()
        >>> simulate(resultfile="a.mat")
        >>> simulate(simflags="-noEventEmit -noRestart -override=e=0.3,g=10) set runtime simulation flags
        >>> simulate(simflags="-noEventEmit -noRestart" ,overrideaux="outputFormat=csv,variableFilter=.*") 
        """
        if(resultfile is None):
            r=""
            self.resultfile = "".join([self.modelName, "_res.mat"])
        else:
            r=" -r=" + resultfile
            self.resultfile = resultfile

        # allow runtime simulation flags from user input
        if(simflags is None):
            simflags=""
        else:
            simflags=" " + simflags;

        if (self._override_variables or self._simulate_options_override):
            tmpdict=self._override_variables.copy()
            tmpdict.update(self._simulate_options_override)
            values1 = ','.join("%s=%s" % (key, val) for (key, val) in list(tmpdict.items()))
            override =" -override=" + values1
        else:
            override =""
        # add override flags not parameters or simulation options
        if overrideaux:
            if override:
                override = override + "," + overrideaux
            else:
                override = " -override=" + overrideaux

        if (self.inputFlag):  # if model has input quantities
            for i in self._inputs:
                val=self._inputs[i]
                if(val==None):
                    val=[(float(self._simulate_options["startTime"]), 0.0), (float(self._simulate_options["stopTime"]), 0.0)]
                    self._inputs[i]=[(float(self._simulate_options["startTime"]), 0.0), (float(self._simulate_options["stopTime"]), 0.0)]
                if float(self._simulate_options["startTime"]) != val[0][0]:
                    print("!!! startTime not matched for Input ",i)
                    return
                if float(self._simulate_options["stopTime"]) != val[-1][0]:
                    print("!!! stopTime not matched for Input ",i)
                    return
                if val[0][0] < float(self._simulate_options["startTime"]):
                    print('Input time value is less than simulation startTime for inputs', i)
                    return
            # self.__simInput()  # create csv file  # commented by Joerg
            csvinput=" -csvInput=" + self.csvFile
        else:
            csvinput=""

        if self.xmlFile is not None:
            cwd_current = os.getcwd()
            os.chdir(os.path.join(os.path.dirname(self.xmlFile)))

        if (platform.system() == "Windows"):
            getExeFile = os.path.join(os.getcwd(), '{}.{}'.format(self.modelName, "exe")).replace("\\", "/")
        else:
            getExeFile = os.path.join(os.getcwd(), self.modelName).replace("\\", "/")

        out = None
        if (os.path.exists(getExeFile)):
            if not os.access(getExeFile, os.X_OK):  # ensure that executable permission is set
                st = os.stat(getExeFile)
                os.chmod(getExeFile, st.st_mode | stat.S_IEXEC)
            cmd = getExeFile + override + csvinput + r + simflags
            if (platform.system() == "Windows"):
                omhome = os.path.join(os.environ.get("OPENMODELICAHOME"))
                dllPath = os.path.join(omhome, "bin").replace("\\", "/") + os.pathsep + os.path.join(omhome, "lib/omc").replace("\\", "/") + os.pathsep + os.path.join(omhome, "lib/omc/cpp").replace("\\", "/") +  os.pathsep + os.path.join(omhome, "lib/omc/omsicpp").replace("\\", "/")
                my_env = os.environ.copy()
                my_env["PATH"] = dllPath + os.pathsep + my_env["PATH"]
                p = subprocess.Popen(cmd, env=my_env)
                p.wait()
                p.terminate()
            else:
                print(str(cmd))
                p = subprocess.run(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out = p.stdout # .read()
            self.simulationFlag = True
            if self.xmlFile is not None:
                os.chdir(cwd_current)

        else:
            raise ModelicaSystemError("Modelica application file not generated yet")
        return out

    @staticmethod
    def _prepare_input_data(
            input_args: Any,
            input_kwargs: dict[str, Any],
    ) -> dict[str, str]:
        """
        Convert raw input to a structured dictionary {'key1': 'value1', 'key2': 'value2'}.
        """

        def prepare_str(str_in: str) -> dict[str, str]:
            str_in = str_in.replace(" ", "")
            key_val_list: list[str] = str_in.split("=")
            if len(key_val_list) != 2:
                raise ModelicaSystemError(f"Invalid 'key=value' pair: {str_in}")

            input_data_from_str: dict[str, str] = {key_val_list[0]: key_val_list[1]}

            return input_data_from_str

        input_data: dict[str, str] = {}

        for input_arg in input_args:
            if isinstance(input_arg, str):
                warnings.warn(message="The definition of values to set should use a dictionary, "
                                      "i.e. {'key1': 'val1', 'key2': 'val2', ...}. Please convert all cases which "
                                      "use a string ('key=val') or list ['key1=val1', 'key2=val2', ...]",
                              category=DeprecationWarning,
                              stacklevel=3)
                input_data = input_data | prepare_str(input_arg)
            elif isinstance(input_arg, list):
                warnings.warn(message="The definition of values to set should use a dictionary, "
                                      "i.e. {'key1': 'val1', 'key2': 'val2', ...}. Please convert all cases which "
                                      "use a string ('key=val') or list ['key1=val1', 'key2=val2', ...]",
                              category=DeprecationWarning,
                              stacklevel=3)

                for item in input_arg:
                    if not isinstance(item, str):
                        raise ModelicaSystemError(f"Invalid input data type for set*() function: {type(item)}!")
                    input_data = input_data | prepare_str(item)
            elif isinstance(input_arg, dict):
                input_data = input_data | input_arg
            else:
                raise ModelicaSystemError(f"Invalid input data type for set*() function: {type(input_arg)}!")

        if len(input_kwargs):
            for key, val in input_kwargs.items():
                # ensure all values are strings to align it on one type: dict[str, str]
                if not isinstance(val, str):
                    # spaces have to be removed as setInput() could take list of tuples as input and spaces would
                    # result in an error on recreating the input data
                    str_val = str(val).replace(' ', '')
                else:
                    str_val = val
                if ' ' in key or ' ' in str_val:
                    raise ModelicaSystemError(f"Spaces not allowed in key/value pairs: {repr(key)} = {repr(val)}!")
                input_data[key] = str_val

        return input_data

    def _set_method_helper(
            self,
            inputdata: dict[str, str],
            classdata: dict[str, Any],
            datatype: str,
            overridedata: Optional[dict[str, str]] = None,
    ) -> bool:
        """
        Helper function for:
        * setParameter()
        * setContinuous()
        * setSimulationOptions()
        * setLinearizationOption()
        * setOptimizationOption()
        * setInputs()

        Parameters
        ----------
        inputdata
            string or list of string given by user
        classdata
            dict() containing the values of different variables (eg: parameter, continuous, simulation parameters)
        datatype
            type identifier (eg; continuous, parameter, simulation, linearization, optimization)
        overridedata
            dict() which stores the new override variables list,
        """

        for key, val in inputdata.items():
            if key not in classdata:
                raise ModelicaSystemError(f"Invalid variable for type {repr(datatype)}: {repr(key)}")

            if datatype == "parameter" and not self.isParameterChangeable(key):
                raise ModelicaSystemError(f"It is not possible to set the parameter {repr(key)}. It seems to be "
                                          "structural, final, protected, evaluated or has a non-constant binding. "
                                          "Use sendExpression(...) and rebuild the model using buildModel() API; "
                                          "command to set the parameter before rebuilding the model: "
                                          "sendExpression(\"setParameterValue("
                                          f"{self._model_name}, {key}, {val if val is not None else '<?value?>'}"
                                          ")\").")

            classdata[key] = val
            if overridedata is not None:
                overridedata[key] = val

        return True

    def isParameterChangeable(
            self,
            name: str,
    ) -> bool:
        """
        Return if the parameter defined by name is changeable (= non-structural; can be modified without the need to
        recompile the model).
        """
        q = self.getQuantities(name)
        if q[0]["changeable"] == "false":
            return False
        return True

    def setContinuous(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set continuous values. It can be called:
        with a sequence of continuous name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setContinuous("Name=value")  # depreciated
        >>> setContinuous(["Name1=value1","Name2=value2"])  # depreciated

        >>> setContinuous(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setContinuous(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._continuous,
            datatype="continuous",
            overridedata=self._override_variables)

    def setParameters(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set parameter values. It can be called:
        with a sequence of parameter name and assigning corresponding value as arguments as show in the example below:
        usage
        >>> setParameters("Name=value")  # depreciated
        >>> setParameters(["Name1=value1","Name2=value2"])  # depreciated

        >>> setParameters(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setParameters(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._params,
            datatype="parameter",
            overridedata=self._override_variables)

    def setSimulationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set simulation options. It can be called:
        with a sequence of simulation options name and assigning corresponding values as arguments as show in the
        example below:
        usage
        >>> setSimulationOptions("Name=value")  # depreciated
        >>> setSimulationOptions(["Name1=value1","Name2=value2"])  # depreciated

        >>> setSimulationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setSimulationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._simulate_options,
            datatype="simulation-option",
            overridedata=self._simulate_options_override)

    def setOptimizationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set optimization options. It can be called:
        with a sequence of optimization options name and assigning corresponding values as arguments as show in the
        example below:
        usage
        >>> setOptimizationOptions("Name=value")  # depreciated
        >>> setOptimizationOptions(["Name1=value1","Name2=value2"])  # depreciated

        >>> setOptimizationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setOptimizationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._optimization_options,
            datatype="optimization-option",
            overridedata=None)
