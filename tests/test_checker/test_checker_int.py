import pytest
from utils.type_checker import valint, InvalidContractError


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
