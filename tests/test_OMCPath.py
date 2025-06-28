import OMPython


def test_OMCPath_docker():
    omcp = OMPython.OMCProcessDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    om = OMPython.OMCSessionZMQ(omc_process=omcp)
    assert om.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    p1 = om.omcpath('/tmp')
    assert str(p1) == "/tmp"
    p2 = p1 / 'test.txt'
    assert str(p2) == "/tmp/test.txt"
    assert p2.write_text('test')
    assert p2.read_text() == "test"
    assert p2.is_file()
    assert p2.parent.is_dir()
    assert p2.unlink()
    assert p2.is_file() == False

    del omcp
    del om


if __name__ == '__main__':
    test_OMCPath_docker()
    print('DONE')