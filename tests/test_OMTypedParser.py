import OMPython

parser = OMPython.OMTypedParser.om_parser_typed


def test_newline_behaviour():
    pass


def test_boolean():
    # TODO: why does these fail?
    # assert parser('TRUE') is True
    # assert parser('True') is True
    assert parser('true') is True
    # TODO: why does these fail?
    # assert parser('FALSE') is False
    # assert parser('False') is False
    assert parser('false') is False


def test_int():
    assert parser('2') == 2
    assert type(parser('1')) == int
    assert type(parser('123123123123123123232323')) == int
    assert type(parser('9223372036854775808')) == int


def test_float():
    assert type(parser('1.2e3')) == float


def test_dict():
    # TODO: why does it fail?
    # assert type(parser('{"a": "b"}')) == dict
    pass


def test_ident():
    assert parser('blabla2') == "blabla2"


def test_empty():
    assert parser('') is None


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
    results = parser(testdata)
    assert results == expected
