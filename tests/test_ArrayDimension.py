import OMPython
import tempfile, shutil, os
import pytest


"""
do not change the prefix class name, the class name should have prefix "Test"
according to the documenation of pytest
"""
class Test_ArrayDimension:

    def test_ArrayDimension(self):
        omc = OMPython.OMCSessionZMQ()

        ## create a temp dir for each session
        tempdir = tempfile.mkdtemp()
        if not os.path.exists(tempdir):
            return print(tempdir, " cannot be created")

        tempdirExp="".join(["cd(","\"",tempdir,"\"",")"]).replace("\\","/")
        omc.sendExpression(tempdirExp)

        omc.sendExpression("loadString(\"model A Integer x[5+1,1+6]; end A;\")")
        omc.sendExpression("getErrorString()")

        result = omc.sendExpression("getComponents(A)")
        assert result[0][-1] == (6,7), f"array dimension does not match the expected value. Got: {result[0][-1]}, Expected: {(6, 7)}"

        omc.__del__()
        shutil.rmtree(tempdir, ignore_errors= True)

