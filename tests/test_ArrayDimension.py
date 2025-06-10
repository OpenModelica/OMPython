import OMPython


def test_ArrayDimension(tmp_path):
    omc = OMPython.OMCSessionZMQ()

    omc.sendExpression(f'cd("{tmp_path.as_posix()}")')

    omc.sendExpression('loadString("model A Integer x[5+1,1+6]; end A;")')
    omc.sendExpression("getErrorString()")

    result = omc.sendExpression("getComponents(A)")
    assert result[0][-1] == (6, 7), "array dimension does not match"

    omc.sendExpression('loadString("model A Integer y = 5; Integer x[y+1,1+9]; end A;")')
    omc.sendExpression("getErrorString()")

    result = omc.sendExpression("getComponents(A)")
    assert result[-1][-1] == ('y+1', 10), "array dimension does not match"
