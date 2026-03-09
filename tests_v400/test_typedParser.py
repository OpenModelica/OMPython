from OMPython import OMTypedParser

typeCheck = OMTypedParser.parseString


def test_newline_behaviour():
    pass


def test_boolean():
    assert typeCheck('true') is True
    assert typeCheck('false') is False


def test_int():
    assert typeCheck('2') == 2
    assert type(typeCheck('1')) == int
    assert type(typeCheck('123123123123123123232323')) == int
    assert type(typeCheck('9223372036854775808')) == int


def test_float():
    assert type(typeCheck('1.2e3')) == float


def test_ident():
    assert typeCheck('blabla2') == "blabla2"


def test_empty():
    assert typeCheck('') is None


def test_str():
    pass


def test_UnStringable():
    pass


def test_everything():
    # this test used to be in OMTypedParser.py's main()
    testdata = """
   (1.0,{{1,true,3},{"4\\"
",5.9,6,NONE ( )},record ABC
  startTime = ErrorLevel.warning,
  'stop*Time' = SOME(1.0)
end ABC;})
    """
    expected = (1.0, ((1, True, 3), ('4"\n', 5.9, 6, None), {"'stop*Time'": 1.0, 'startTime': 'ErrorLevel.warning'}))
    results = typeCheck(testdata)
    assert results == expected
