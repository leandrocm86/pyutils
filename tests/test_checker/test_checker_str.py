import pytest
from typeguard import TypeCheckError
import mods.checker as ck


def test_checker_str_valid():
    # Test with a valid string
    ck.strok("hello", length=5)


def test_checker_str_invalid_type():
    # Test with an invalid type
    with pytest.raises(TypeCheckError):
        ck.strok(5)  # type: ignore


def test_checker_str_invalid_length():
    # Test with an invalid length
    with pytest.raises(ck.InvalidContractError):
        ck.strok("hello", length=10)


def test_checker_str_minlen():
    # Test with a minimum length
    ck.strok("hello", minlen=4)


def test_checker_str_minlen_invalid():
    # Test with an invalid minimum length
    with pytest.raises(ck.InvalidContractError):
        ck.strok("he", minlen=3)


def test_checker_str_maxlen():
    # Test with a maximum length
    ck.strok("hello", maxlen=10)


def test_checker_str_maxlen_invalid():
    # Test with an invalid maximum length
    with pytest.raises(ck.InvalidContractError):
        ck.strok("hello world", maxlen=5)


def test_checker_str_upper():
    # Test with an uppercase string
    ck.strok("HELLO", upper=True)


def test_checker_str_upper_invalid():
    # Test with a non-uppercase string
    with pytest.raises(ck.InvalidContractError):
        ck.strok("Hello", upper=True)


def test_checker_str_lower():
    # Test with a lowercase string
    ck.strok("hello", lower=True)


def test_checker_str_lower_invalid():
    # Test with a non-lowercase string
    with pytest.raises(ck.InvalidContractError):
        ck.strok("Hello", lower=True)


def test_checker_str_regex():
    # Test with a regex pattern
    ck.strok("hello@gmail.com", regex=r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def test_checker_str_regex_invalid():
    # Test with an invalid regex pattern
    with pytest.raises(ck.InvalidContractError):
        ck.strok("hello", regex=r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def test_checker_str_domain():
    # Test with a domain name
    ck.strok("gmail.com", domain={"gmail.com", "yahoo.com", "hotmail.com"})
    ck.strok("gmail.com", domain=["gmail.com", "yahoo.com", "hotmail.com"])
    ck.strok("gmail.com", domain=("gmail.com", "yahoo.com", "hotmail.com"))


def test_checker_str_domain_invalid():
    # Test with an invalid domain name
    with pytest.raises(ck.InvalidContractError):
        ck.strok("gmail.com", domain={"yahoo.com", "hotmail.com"})


def test_checker_str_custom():
    # Test with a custom function
    def is_hello(value: str):
        return value == "hello"

    ck.strok("hello", custom=lambda s: s == "hello")
    ck.strok("hello", custom=is_hello)


def test_checker_str_custom_invalid():
    # Test with an invalid custom function
    with pytest.raises(ck.InvalidContractError):
        ck.strok("hello", custom=lambda s: s == "world")
