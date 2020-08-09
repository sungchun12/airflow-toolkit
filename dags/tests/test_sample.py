# content of test_sample.py
def inc(x):
    return x + 1


def test_answer():
    assert inc(3) == 4


def f(name):
    print("hello {}".format(name))


def test_f(capfd):
    f("Tom")

    out, err = capfd.readouterr()
    assert out == "hello Tom\n"
