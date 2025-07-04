import pytest
from mods.checker import intok, InvalidContractError


def test_isint_valid():
    intok(5)
    intok(0)
    intok(-10)


def test_isint_invalid_type():
    with pytest.raises(TypeError):
        intok("hello")  # type: ignore


def test_isint_min():
    intok(5, min=5)
    with pytest.raises(InvalidContractError):
        intok(4, min=5)


def test_isint_max():
    intok(5, max=5)
    with pytest.raises(InvalidContractError):
        intok(6, max=5)


def test_isint_domain():
    intok(3, domain=[1, 2, 3, 4, 5])
    with pytest.raises(InvalidContractError):
        intok(6, domain=[1, 2, 3, 4, 5])


def test_isint_custom():
    def custom_check(x: int):
        return x > 0
    intok(5, custom=custom_check)
    intok(1, custom=lambda x: x > 0)


def test_isint_custom_invalid():
    with pytest.raises(InvalidContractError):
        intok(-1, custom=lambda x: x > 0)
