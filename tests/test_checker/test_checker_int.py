import pytest
from utils.type_checker import valint, InvalidContractError


def test_isint_valid():
    valint(5)
    valint(0)
    valint(-10)


def test_isint_invalid_type():
    with pytest.raises(TypeError):
        valint("hello")  # type: ignore


def test_isint_min():
    valint(5, min=5)
    with pytest.raises(InvalidContractError):
        valint(4, min=5)


def test_isint_max():
    valint(5, max=5)
    with pytest.raises(InvalidContractError):
        valint(6, max=5)


def test_isint_domain():
    valint(3, domain=[1, 2, 3, 4, 5])
    with pytest.raises(InvalidContractError):
        valint(6, domain=[1, 2, 3, 4, 5])


def test_isint_custom():
    def custom_check(x: int):
        return x > 0
    valint(5, custom=custom_check)
    valint(1, custom=lambda x: x > 0)


def test_isint_custom_invalid():
    with pytest.raises(InvalidContractError):
        valint(-1, custom=lambda x: x > 0)
