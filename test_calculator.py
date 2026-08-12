import pytest
from calculator import *


def test_add():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-5, 2) == -3


def test_subtract():
    assert subtract(10, 4) == 6


def test_subtract_negative():
    assert subtract(2, 5) == -3


def test_multiply():
    assert multiply(5, 4) == 20


def test_multiply_zero():
    assert multiply(10, 0) == 0


def test_divide():
    assert divide(10, 2) == 5


def test_divide_float():
    assert divide(5, 2) == 2.5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)


def test_even():
    assert is_even(10)


def test_odd():
    assert not is_even(11)


def test_square():
    assert square(5) == 25



import os


def test_autoheal_flaky():
    """
    Simulated flaky test.

    The first AUTOHEAL retry fails.
    Subsequent runs succeed using a workspace marker.
    """
    marker = ".autoheal_flaky_once"

    if os.getenv("AUTOHEAL_TEST") == "true":
        if not os.path.exists(marker):
            with open(marker, "w") as file:
                file.write("failed")

            assert False, "AUTOHEAL_FLAKY_TEST"