# -*- coding: utf-8 -*-
"""
Definition of an OMC session.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
import warnings

import pyparsing

from OMPython.om_session_abc import (
    OMPathABC,
    OMSessionABC,
    OMSessionException,
)
from OMPython.om_session_omc import (
    DockerPopen,
    OMCSessionABC,
    OMCSessionDocker,
    OMCSessionDockerContainer,
    OMCSessionLocal,
    OMCSessionPort,
    OMCSessionWSL,
)


# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class OMCSessionException(OMSessionException):
    """
    Just a compatibility layer ...
    """


class OMCSessionCmd:
    """
    Implementation of Open Modelica Compiler API functions. Depreciated!
    """

    def __init__(self, session: OMSessionABC, readonly: bool = False):
        warnings.warn(
            message="The class OMCSessionCMD is depreciated and will be removed in future versions; "
                    "please use OMCSession*.sendExpression(...) instead!",
            category=DeprecationWarning,
            stacklevel=2,
        )

        if not isinstance(session, OMSessionABC):
            raise OMSessionException("Invalid OMC process definition!")
        self._session = session
        self._readonly = readonly
        self._omc_cache: dict[tuple[str, bool], Any] = {}

    def _ask(self, question: str, opt: Optional[list[str]] = None, parsed: bool = True):

        if opt is None:
            expression = question
        elif isinstance(opt, list):
            expression = f"{question}({','.join([str(x) for x in opt])})"
        else:
            raise OMSessionException(f"Invalid definition of options for {repr(question)}: {repr(opt)}")

        p = (expression, parsed)

        if self._readonly and question != 'getErrorString':
            # can use cache if readonly
            if p in self._omc_cache:
                return self._omc_cache[p]

        try:
            res = self._session.sendExpression(expression, parsed=parsed)
        except OMSessionException as ex:
            raise OMSessionException(f"OMC _ask() failed: {expression} (parsed={parsed})") from ex

        # save response
        self._omc_cache[p] = res

        return res

    # TODO: Open Modelica Compiler API functions. Would be nice to generate these.
    def loadFile(self, filename):
        return self._ask(question='loadFile', opt=[f'"{filename}"'])

    def loadModel(self, className):
        return self._ask(question='loadModel', opt=[className])

    def isModel(self, className):
        return self._ask(question='isModel', opt=[className])

    def isPackage(self, className):
        return self._ask(question='isPackage', opt=[className])

    def isPrimitive(self, className):
        return self._ask(question='isPrimitive', opt=[className])

    def isConnector(self, className):
        return self._ask(question='isConnector', opt=[className])

    def isRecord(self, className):
        return self._ask(question='isRecord', opt=[className])

    def isBlock(self, className):
        return self._ask(question='isBlock', opt=[className])

    def isType(self, className):
        return self._ask(question='isType', opt=[className])

    def isFunction(self, className):
        return self._ask(question='isFunction', opt=[className])

    def isClass(self, className):
        return self._ask(question='isClass', opt=[className])

    def isParameter(self, className):
        return self._ask(question='isParameter', opt=[className])

    def isConstant(self, className):
        return self._ask(question='isConstant', opt=[className])

    def isProtected(self, className):
        return self._ask(question='isProtected', opt=[className])

    def getPackages(self, className="AllLoadedClasses"):
        return self._ask(question='getPackages', opt=[className])

    def getClassRestriction(self, className):
        return self._ask(question='getClassRestriction', opt=[className])

    def getDerivedClassModifierNames(self, className):
        return self._ask(question='getDerivedClassModifierNames', opt=[className])

    def getDerivedClassModifierValue(self, className, modifierName):
        return self._ask(question='getDerivedClassModifierValue', opt=[className, modifierName])

    def typeNameStrings(self, className):
        return self._ask(question='typeNameStrings', opt=[className])

    def getComponents(self, className):
        return self._ask(question='getComponents', opt=[className])

    def getClassComment(self, className):
        try:
            return self._ask(question='getClassComment', opt=[className])
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getClassComment(%s)' failed; OMTypedParser error: %s",
                           className, ex.msg)
            return 'No description available'

    def getNthComponent(self, className, comp_id):
        """ returns with (type, name, description) """
        return self._ask(question='getNthComponent', opt=[className, comp_id])

    def getNthComponentAnnotation(self, className, comp_id):
        return self._ask(question='getNthComponentAnnotation', opt=[className, comp_id])

    def getImportCount(self, className):
        return self._ask(question='getImportCount', opt=[className])

    def getNthImport(self, className, importNumber):
        # [Path, id, kind]
        return self._ask(question='getNthImport', opt=[className, importNumber])

    def getInheritanceCount(self, className):
        return self._ask(question='getInheritanceCount', opt=[className])

    def getNthInheritedClass(self, className, inheritanceDepth):
        return self._ask(question='getNthInheritedClass', opt=[className, inheritanceDepth])

    def getParameterNames(self, className):
        try:
            return self._ask(question='getParameterNames', opt=[className])
        except KeyError as ex:
            logger.warning('OMPython error: %s', ex)
            # FIXME: OMC returns with a different structure for empty parameter set
            return []

    def getParameterValue(self, className, parameterName):
        try:
            return self._ask(question='getParameterValue', opt=[className, parameterName])
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getParameterValue(%s, %s)' failed; OMTypedParser error: %s",
                           className, parameterName, ex.msg)
            return ""

    def getComponentModifierNames(self, className, componentName):
        return self._ask(question='getComponentModifierNames', opt=[className, componentName])

    def getComponentModifierValue(self, className, componentName):
        return self._ask(question='getComponentModifierValue', opt=[className, componentName])

    def getExtendsModifierNames(self, className, componentName):
        return self._ask(question='getExtendsModifierNames', opt=[className, componentName])

    def getExtendsModifierValue(self, className, extendsName, modifierName):
        return self._ask(question='getExtendsModifierValue', opt=[className, extendsName, modifierName])

    def getNthComponentModification(self, className, comp_id):
        # FIXME: OMPython exception Results KeyError exception

        # get {$Code(....)} field
        # \{\$Code\((\S*\s*)*\)\}
        value = self._ask(question='getNthComponentModification', opt=[className, comp_id], parsed=False)
        value = value.replace("{$Code(", "")
        return value[:-3]
        # return self.re_Code.findall(value)

    # function getClassNames
    #   input TypeName class_ = $Code(AllLoadedClasses);
    #   input Boolean recursive = false;
    #   input Boolean qualified = false;
    #   input Boolean sort = false;
    #   input Boolean builtin = false "List also builtin classes if true";
    #   input Boolean showProtected = false "List also protected classes if true";
    #   output TypeName classNames[:];
    # end getClassNames;
    def getClassNames(self, className=None, recursive=False, qualified=False, sort=False, builtin=False,
                      showProtected=False):
        opt = [className] if className else [] + [f'recursive={str(recursive).lower()}',
                                                  f'qualified={str(qualified).lower()}',
                                                  f'sort={str(sort).lower()}',
                                                  f'builtin={str(builtin).lower()}',
                                                  f'showProtected={str(showProtected).lower()}']
        return self._ask(question='getClassNames', opt=opt)


class OMCSessionZMQ(OMSessionABC):
    """
    This class is a compatibility layer for the new schema using OMCSession* classes.
    """

    def __init__(
            self,
            timeout: float = 10.00,
            omhome: Optional[str] = None,
            omc_process: Optional[OMCSessionABC] = None,
    ) -> None:
        """
        Initialisation for OMCSessionZMQ
        """
        warnings.warn(message="The class OMCSessionZMQ is depreciated and will be removed in future versions; "
                              "please use OMCProcess* classes instead!",
                      category=DeprecationWarning,
                      stacklevel=2)

        if omc_process is None:
            omc_process = OMCSessionLocal(omhome=omhome, timeout=timeout)
        elif not isinstance(omc_process, OMCSessionABC):
            raise OMSessionException("Invalid definition of the OMC process!")
        self.omc_process = omc_process

        super().__init__(timeout=timeout)

    def __del__(self):
        if hasattr(self, 'omc_process'):
            del self.omc_process

    @staticmethod
    def escape_str(value: str) -> str:
        """
        Escape a string such that it can be used as string within OMC expressions, i.e. escape all double quotes.
        """
        return OMCSessionABC.escape_str(value=value)

    def omcpath(self, *path) -> OMPathABC:
        """
        Create an OMCPath object based on the given path segments and the current OMC process definition.
        """
        return self.omc_process.omcpath(*path)

    def omcpath_tempdir(self, tempdir_base: Optional[OMPathABC] = None) -> OMPathABC:
        """
        Get a temporary directory using OMC. It is our own implementation as non-local usage relies on OMC to run all
        filesystem related access.
        """
        return self.omc_process.omcpath_tempdir(tempdir_base=tempdir_base)

    def execute(self, command: str):
        return self.omc_process.execute(command=command)

    def sendExpression(self, command: str, parsed: bool = True) -> Any:  # pylint: disable=W0237
        """
        Send an expression to the OMC server and return the result.

        The complete error handling of the OMC result is done within this method using 'getMessagesStringInternal()'.
        Caller should only check for OMCSessionException.

        Compatibility: 'command' was renamed to 'expr'
        """
        return self.omc_process.sendExpression(expr=command, parsed=parsed)

    def get_version(self) -> str:
        return self.omc_process.get_version()

    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        return self.omc_process.model_execution_prefix(cwd=cwd)

    def set_workdir(self, workdir: OMPathABC) -> None:
        return self.omc_process.set_workdir(workdir=workdir)


DummyPopen = DockerPopen
OMCProcessLocal = OMCSessionLocal
OMCProcessPort = OMCSessionPort
OMCProcessDocker = OMCSessionDocker
OMCProcessDockerContainer = OMCSessionDockerContainer
OMCProcessWSL = OMCSessionWSL
