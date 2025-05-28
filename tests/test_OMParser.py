from OMPython import OMParser

typeCheck = OMParser.typeCheck


def test_newline_behaviour():
    pass


def test_boolean():
    assert typeCheck('TRUE') is True
    assert typeCheck('True') is True
    assert typeCheck('true') is True
    assert typeCheck('FALSE') is False
    assert typeCheck('False') is False
    assert typeCheck('false') is False


def test_int():
    assert typeCheck('2') == 2
    assert type(typeCheck('1')) == int
    assert type(typeCheck('123123123123123123232323')) == int
    assert type(typeCheck('9223372036854775808')) == int


def test_float():
    assert type(typeCheck('1.2e3')) == float


# def test_dict():
#     assert type(typeCheck('{"a": "b"}')) == dict


def test_ident():
    assert typeCheck('blabla2') == "blabla2"


def test_str():
    pass


def test_UnStringable():
    pass
