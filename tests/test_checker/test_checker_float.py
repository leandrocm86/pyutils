import pytest
from mods.type_checker import valfloat, InvalidContractError


def test_isfloat_valid():
    valfloat(5.5)
    valfloat(0.0)
    valfloat(-10.2)


def test_isfloat_invalid_type():
    with pytest.raises(TypeError):
        valfloat("hello")  # type: ignore


def test_isfloat_min():
    valfloat(5.5, min=5.5)
    with pytest.raises(InvalidContractError):
        valfloat(3.3, min=5.5)


def test_isfloat_max():
    valfloat(5.5, max=5.5)
    with pytest.raises(InvalidContractError):
        valfloat(7.7, max=5.5)


def test_isfloat_domain():
    valfloat(5.5, domain=[1.1, 2.2, 3.3, 4.4, 5.5])
    with pytest.raises(InvalidContractError):
        valfloat(6.6, domain=[1.1, 2.2, 3.3, 4.4, 5.5])


def test_isfloat_custom():
    def custom_check(x: float):
        return x > 0
    valfloat(5.5, custom=custom_check)
    valfloat(1.1, custom=lambda x: x > 0)


def test_isfloat_custom_invalid():
    with pytest.raises(InvalidContractError):
        valfloat(-1.1, custom=lambda x: x > 0)
