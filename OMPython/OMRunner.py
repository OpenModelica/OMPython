import os
import stat
import platform
import subprocess
import shlex
from typing import Optional
import xml.etree.ElementTree as ET
import logging

# Import base class and exception
from OMPython.OMBase import ModelicaSystemBase, ModelicaSystemError

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemRunner(ModelicaSystemBase):
    def __init__(
            self,
            runpath: str,
            modelname: Optional[str] = None,
            variableFilter: Optional[list] = None,
    ) -> None:
        if modelname is None:
            raise ModelicaSystemError("Missing model name!")

        # Initialize base class
        super().__init__()

        self.runpath = os.path.abspath(runpath)

        print(self.runpath)
        exefile = os.path.join(self.runpath, modelname)
        if not os.path.isfile(exefile):
            raise ModelicaSystemError("Executable model file not found in {0}".format(exefile))

        self.xmlFileName = modelname + "_init.xml"
        self.xmlFile = os.path.join(self.runpath, self.xmlFileName)
        self._model_name = modelname  # Model class name
        self.inputFlag = False  # for model with input quantity
        self.simulationFlag = False  # if the model is simulated?
        self.outputFlag = False
        self.csvFile = ''  # for storing inputs condition
        self.resultfile = ""  # for storing result file
        self.variableFilter = variableFilter
        self._xmlparse(xml_file=self.xmlFile)
        self._variable_filter: Optional[str] = None
        print("Init done")

    def _xmlparse(self, xml_file: str):
        if not os.path.isfile(xml_file):
            raise ModelicaSystemError(f"XML file not generated: {xml_file}")

        # OMRunner uses ET.parse directly on the file path
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Delegate population to base class
        self._populate_from_xml_root(root)

    def simulate(self, resultfile=None, simflags=None, overrideaux=None):  # 11
        """This method simulates model according to the simulation options."""
        if resultfile is None:
            r = ""
            self.resultfile = "".join([self._model_name, "_res.mat"])
        else:
            r = " -r=" + resultfile
            self.resultfile = resultfile

        # allow runtime simulation flags from user input
        if simflags is None:
            simflags = ""
        else:
            simflags = " " + simflags

        if (self._override_variables or self._simulate_options_override):
            tmpdict = self._override_variables.copy()
            tmpdict.update(self._simulate_options_override)
            values1 = ','.join("%s=%s" % (key, val) for (key, val) in list(tmpdict.items()))
            override = " -override=" + values1
        else:
            override = ""
        # add override flags not parameters or simulation options
        if overrideaux:
            if override:
                override = override + "," + overrideaux
            else:
                override = " -override=" + overrideaux

        if (self.inputFlag):  # if model has input quantities
            for i in self._inputs:
                val = self._inputs[i]
                if val is None:
                    val = [
                        (float(self._simulate_options["startTime"]), 0.0),
                        (float(self._simulate_options["stopTime"]), 0.0)]
                    self._inputs[i] = [
                        (float(self._simulate_options["startTime"]), 0.0),
                        (float(self._simulate_options["stopTime"]), 0.0)]
                if float(self._simulate_options["startTime"]) != val[0][0]:
                    print("!!! startTime not matched for Input ", i)
                    return
                if float(self._simulate_options["stopTime"]) != val[-1][0]:
                    print("!!! stopTime not matched for Input ", i)
                    return
                if val[0][0] < float(self._simulate_options["startTime"]):
                    print('Input time value is less than simulation startTime for inputs', i)
                    return
            # self.__simInput()  # create csv file  # commented by Joerg
            csvinput = " -csvInput=" + self.csvFile
        else:
            csvinput = ""

        if self.xmlFile is not None:
            cwd_current = os.getcwd()
            os.chdir(os.path.join(os.path.dirname(self.xmlFile)))

        if (platform.system() == "Windows"):
            getExeFile = os.path.join(os.getcwd(), '{}.{}'.format(self._model_name, "exe")).replace("\\", "/")
        else:
            getExeFile = os.path.join(os.getcwd(), self._model_name).replace("\\", "/")

        out = None
        if (os.path.exists(getExeFile)):
            if not os.access(getExeFile, os.X_OK):  # ensure that executable permission is set
                st = os.stat(getExeFile)
                os.chmod(getExeFile, st.st_mode | stat.S_IEXEC)
            cmd = getExeFile + override + csvinput + r + simflags
            if (platform.system() == "Windows"):
                omhome = os.path.join(os.environ.get("OPENMODELICAHOME"))
                dllPath = os.path.join(omhome, "bin").replace("\\", "/") + os.pathsep + \
                    os.path.join(omhome, "lib/omc").replace("\\", "/") + os.pathsep + \
                    os.path.join(omhome, "lib/omc/cpp").replace("\\", "/") + os.pathsep + \
                    os.path.join(omhome, "lib/omc/omsicpp").replace("\\", "/")
                my_env = os.environ.copy()
                my_env["PATH"] = dllPath + os.pathsep + my_env["PATH"]
                p = subprocess.Popen(cmd, env=my_env)
                p.wait()
                p.terminate()
            else:
                print(str(cmd))
                p = subprocess.run(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out = p.stdout  # .read()
            self.simulationFlag = True
            if self.xmlFile is not None:
                os.chdir(cwd_current)

        else:
            raise ModelicaSystemError("Modelica application file not generated yet")
        return out
