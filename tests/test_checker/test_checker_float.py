import pytest
from typeguard import TypeCheckError
from mods.checker import floatok, InvalidContractError


def test_isfloat_valid():
    floatok(5.5)
    floatok(0.0)
    floatok(-10.2)


def test_isfloat_invalid_type():
    with pytest.raises(TypeCheckError):
        floatok("hello")  # type: ignore


def test_isfloat_min():
    floatok(5.5, min=5.5)
    with pytest.raises(InvalidContractError):
        floatok(3.3, min=5.5)


def test_isfloat_max():
    floatok(5.5, max=5.5)
    with pytest.raises(InvalidContractError):
        floatok(7.7, max=5.5)


def test_isfloat_domain():
    floatok(5.5, domain=[1.1, 2.2, 3.3, 4.4, 5.5])
    with pytest.raises(InvalidContractError):
        floatok(6.6, domain=[1.1, 2.2, 3.3, 4.4, 5.5])


def test_isfloat_custom():
    def custom_check(x: float):
        return x > 0
    floatok(5.5, custom=custom_check)
    floatok(1.1, custom=lambda x: x > 0)


def test_isfloat_custom_invalid():
    with pytest.raises(InvalidContractError):
        floatok(-1.1, custom=lambda x: x > 0)
