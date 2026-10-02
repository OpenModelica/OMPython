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
    OMCSessionABC,
    OMCSessionDocker,
    OMCSessionDockerContainer,
    OMCSessionLocal,
    OMCSessionPort,
    OMCSessionWSL,
)

from OMPython.compatibility_v400 import (
    depreciated_class,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


@depreciated_class(msg="Please use class OMSessionException instead!")
class OMCSessionException(OMSessionException):
    """
    Just a compatibility layer ...
    """


@depreciated_class(msg="Please use OMCSession*.sendExpression(...) instead!")
class OMCSessionCmd:
    """
    Implementation of Open Modelica Compiler API functions. Depreciated!
    """

    def __init__(self, session: OMSessionABC, readonly: bool = False):
        """Initialize the OMC API compatibility wrapper.

        Args:
            session: The OMC session to send expressions to.
            readonly: Whether responses may be served from a cache.
        """
        if not isinstance(session, OMSessionABC):
            raise OMCSessionException("Invalid OMC process definition!")
        self._session = session
        self._readonly = readonly
        self._omc_cache: dict[tuple[str, bool], Any] = {}

    def _ask(self, question: str, opt: Optional[list[str]] = None, parsed: bool = True):
        """Send an OMC API question to the session.

        Args:
            question: The OMC API function name to call.
            opt: Optional list of arguments for the API call.
            parsed: Whether to parse the OMC response.

        Returns:
            The (optionally parsed) OMC response.

        Raises:
            OMSessionException: If the options are invalid or the call fails.
        """
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
        """Load a Modelica file. Deprecated."""
        return self._ask(question='loadFile', opt=[f'"{filename}"'])

    def loadModel(self, className):
        """Load a Modelica model/package. Deprecated."""
        return self._ask(question='loadModel', opt=[className])

    def isModel(self, className):
        """Check if ``className`` is a model. Deprecated."""
        return self._ask(question='isModel', opt=[className])

    def isPackage(self, className):
        """Check if ``className`` is a package. Deprecated."""
        return self._ask(question='isPackage', opt=[className])

    def isPrimitive(self, className):
        """Check if ``className`` is a primitive. Deprecated."""
        return self._ask(question='isPrimitive', opt=[className])

    def isConnector(self, className):
        """Check if ``className`` is a connector. Deprecated."""
        return self._ask(question='isConnector', opt=[className])

    def isRecord(self, className):
        """Check if ``className`` is a record. Deprecated."""
        return self._ask(question='isRecord', opt=[className])

    def isBlock(self, className):
        """Check if ``className`` is a block. Deprecated."""
        return self._ask(question='isBlock', opt=[className])

    def isType(self, className):
        """Check if ``className`` is a type. Deprecated."""
        return self._ask(question='isType', opt=[className])

    def isFunction(self, className):
        """Check if ``className`` is a function. Deprecated."""
        return self._ask(question='isFunction', opt=[className])

    def isClass(self, className):
        """Check if ``className`` is a class. Deprecated."""
        return self._ask(question='isClass', opt=[className])

    def isParameter(self, className):
        """Check if ``className`` is a parameter. Deprecated."""
        return self._ask(question='isParameter', opt=[className])

    def isConstant(self, className):
        """Check if ``className`` is a constant. Deprecated."""
        return self._ask(question='isConstant', opt=[className])

    def isProtected(self, className):
        """Check if ``className`` is protected. Deprecated."""
        return self._ask(question='isProtected', opt=[className])

    def getPackages(self, className="AllLoadedClasses"):
        """Get the loaded packages. Deprecated."""
        return self._ask(question='getPackages', opt=[className])

    def getClassRestriction(self, className):
        """Get the class restriction of ``className``. Deprecated."""
        return self._ask(question='getClassRestriction', opt=[className])

    def getDerivedClassModifierNames(self, className):
        """Get the derived class modifier names. Deprecated."""
        return self._ask(question='getDerivedClassModifierNames', opt=[className])

    def getDerivedClassModifierValue(self, className, modifierName):
        """Get the value of a derived class modifier. Deprecated."""
        return self._ask(question='getDerivedClassModifierValue', opt=[className, modifierName])

    def typeNameStrings(self, className):
        """Get the type name strings of ``className``. Deprecated."""
        return self._ask(question='typeNameStrings', opt=[className])

    def getComponents(self, className):
        """Get the components of ``className``. Deprecated."""
        return self._ask(question='getComponents', opt=[className])

    def getClassComment(self, className):
        """Get the comment of ``className``. Deprecated."""
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
        """Get the annotation of the n-th component. Deprecated."""
        return self._ask(question='getNthComponentAnnotation', opt=[className, comp_id])

    def getImportCount(self, className):
        """Get the number of imports of ``className``. Deprecated."""
        return self._ask(question='getImportCount', opt=[className])

    def getNthImport(self, className, importNumber):
        """Get the n-th import of ``className``. Deprecated."""
        # [Path, id, kind]
        return self._ask(question='getNthImport', opt=[className, importNumber])

    def getInheritanceCount(self, className):
        """Get the number of inherited classes of ``className``. Deprecated."""
        return self._ask(question='getInheritanceCount', opt=[className])

    def getNthInheritedClass(self, className, inheritanceDepth):
        """Get the n-th inherited class of ``className``. Deprecated."""
        return self._ask(question='getNthInheritedClass', opt=[className, inheritanceDepth])

    def getParameterNames(self, className):
        """Get the parameter names of ``className``. Deprecated."""
        try:
            return self._ask(question='getParameterNames', opt=[className])
        except KeyError as ex:
            logger.warning('OMPython error: %s', ex)
            # FIXME: OMC returns with a different structure for empty parameter set
            return []

    def getParameterValue(self, className, parameterName):
        """Get the value of a parameter. Deprecated."""
        try:
            return self._ask(question='getParameterValue', opt=[className, parameterName])
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getParameterValue(%s, %s)' failed; OMTypedParser error: %s",
                           className, parameterName, ex.msg)
            return ""

    def getComponentModifierNames(self, className, componentName):
        """Get the modifier names of a component. Deprecated."""
        return self._ask(question='getComponentModifierNames', opt=[className, componentName])

    def getComponentModifierValue(self, className, componentName):
        """Get the modifier value of a component. Deprecated."""
        return self._ask(question='getComponentModifierValue', opt=[className, componentName])

    def getExtendsModifierNames(self, className, componentName):
        """Get the modifier names of an extends clause. Deprecated."""
        return self._ask(question='getExtendsModifierNames', opt=[className, componentName])

    def getExtendsModifierValue(self, className, extendsName, modifierName):
        """Get the modifier value of an extends clause. Deprecated."""
        return self._ask(question='getExtendsModifierValue', opt=[className, extendsName, modifierName])

    def getNthComponentModification(self, className, comp_id):
        """Get the modification of the n-th component. Deprecated."""
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
        """Get class names, optionally filtered. Deprecated.

        Args:
            className: Name of the class to query (defaults to all loaded classes).
            recursive: Whether to include nested classes.
            qualified: Whether to return qualified names.
            sort: Whether to sort the result.
            builtin: Whether to include built-in classes.
            showProtected: Whether to include protected classes.

        Returns:
            The parsed list of class names.
        """
        opt = [className] if className else [] + [f'recursive={str(recursive).lower()}',
                                                  f'qualified={str(qualified).lower()}',
                                                  f'sort={str(sort).lower()}',
                                                  f'builtin={str(builtin).lower()}',
                                                  f'showProtected={str(showProtected).lower()}']
        return self._ask(question='getClassNames', opt=opt)


@depreciated_class(msg="Please use OMCSession* classes instead!")
class OMCSessionZMQ(OMSessionABC):
    """
    This class is a compatibility layer for the new schema using OMCSession* classes.
    """

    def __init__(
            self,
            timeout: Optional[float] = None,
            omhome: Optional[str] = None,
            omc_process: Optional[OMCSessionABC] = None,
    ) -> None:
        """
        Initialisation for OMCSessionZMQ
        """
        if omc_process is None:
            omc_process = OMCSessionLocal(omhome=omhome, timeout=timeout)
        elif not isinstance(omc_process, OMCSessionABC):
            raise OMSessionException("Invalid definition of the OMC process!")
        self.omc_process = omc_process

        super().__init__(timeout=timeout)

    def __del__(self):
        """Clean up the underlying OMC process."""
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
        """Execute a raw command on the OMC server. Deprecated.

        Args:
            command: The raw OMC expression to execute.

        Returns:
            The unparsed OMC response.
        """
        warnings.warn(
            message="This function is depreciated and will be removed in future versions; "
                    "please use sendExpression() instead",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return self.omc_process.sendExpression(expr=command, parsed=False)

    def sendExpression(
        self,
        command: str,
        parsed: bool = True,
        raise_on_error: bool = True,
    ) -> Any:  # pylint: disable=W0237
        """
        Send an expression to the OMC server and return the result.

        The complete error handling of the OMC result is done within this method using 'getMessagesStringInternal()'.
        Caller should only check for OMCSessionException.

        Compatibility: 'command' was renamed to 'expr'
        """
        return self.omc_process.sendExpression(expr=command, parsed=parsed, raise_on_error=raise_on_error)

    def get_version(self) -> str:
        """Get the version of the OMC server. Deprecated."""
        return self.omc_process.get_version()

    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        """Get the model execution command prefix. Deprecated."""
        return self.omc_process.model_execution_prefix(cwd=cwd)

    def set_workdir(self, workdir: OMPathABC) -> None:
        """Set the working directory. Deprecated."""
        return self.omc_process.set_workdir(workdir=workdir)


@depreciated_class(msg="Please use class OMCSessionLocal instead!")
class OMCProcessLocal(OMCSessionLocal):
    """
    Just a wrapper class; OMCProcessLocal => OMCSessionLocal
    """


@depreciated_class(msg="Please use class OMCSessionPort instead!")
class OMCProcessPort(OMCSessionPort):
    """
    Just a wrapper class; OMCProcessPort => OMCSessionPort
    """


@depreciated_class(msg="Please use class OMCSessionDocker instead!")
class OMCProcessDocker(OMCSessionDocker):
    """
    Just a wrapper class; OMCProcessDocker => OMCSessionDocker
    """


@depreciated_class(msg="Please use class OMCSessionDockerContainer instead!")
class OMCProcessDockerContainer(OMCSessionDockerContainer):
    """
    Just a wrapper class; OMCProcessDockerContainer => OMCSessionDockerContainer
    """


@depreciated_class(msg="Please use class OMCSessionWSL instead!")
class OMCProcessWSL(OMCSessionWSL):
    """
    Just a wrapper class; OMCProcessWSL => OMCSessionWSL
    """
