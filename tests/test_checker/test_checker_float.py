import pytest
from utils.type_checker import valfloat, InvalidContractError


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
