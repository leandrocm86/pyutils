import pytest
import mods.type_checker as ck


def test_checker_str_valid():
    # Test with a valid string
    ck.valstr("hello", length=5)


def test_checker_str_invalid_type():
    # Test with an invalid type
    with pytest.raises(TypeError):
        ck.valstr(5)  # type: ignore


def test_checker_str_invalid_length():
    # Test with an invalid length
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("hello", length=10)


def test_checker_str_minlen():
    # Test with a minimum length
    ck.valstr("hello", minlen=4)


def test_checker_str_minlen_invalid():
    # Test with an invalid minimum length
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("he", minlen=3)


def test_checker_str_maxlen():
    # Test with a maximum length
    ck.valstr("hello", maxlen=10)


def test_checker_str_maxlen_invalid():
    # Test with an invalid maximum length
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("hello world", maxlen=5)


def test_checker_str_upper():
    # Test with an uppercase string
    ck.valstr("HELLO", upper=True)


def test_checker_str_upper_invalid():
    # Test with a non-uppercase string
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("Hello", upper=True)


def test_checker_str_lower():
    # Test with a lowercase string
    ck.valstr("hello", lower=True)


def test_checker_str_lower_invalid():
    # Test with a non-lowercase string
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("Hello", lower=True)


def test_checker_str_regex():
    # Test with a regex pattern
    ck.valstr("hello@gmail.com", regex=r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def test_checker_str_regex_invalid():
    # Test with an invalid regex pattern
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("hello", regex=r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def test_checker_str_domain():
    # Test with a domain name
    ck.valstr("gmail.com", domain={"gmail.com", "yahoo.com", "hotmail.com"})
    ck.valstr("gmail.com", domain=["gmail.com", "yahoo.com", "hotmail.com"])
    ck.valstr("gmail.com", domain=("gmail.com", "yahoo.com", "hotmail.com"))


def test_checker_str_domain_invalid():
    # Test with an invalid domain name
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("gmail.com", domain={"yahoo.com", "hotmail.com"})


def test_checker_str_custom():
    # Test with a custom function
    def is_hello(value: str):
        return value == "hello"

    ck.valstr("hello", custom=lambda s: s == "hello")
    ck.valstr("hello", custom=is_hello)


def test_checker_str_custom_invalid():
    # Test with an invalid custom function
    with pytest.raises(ck.InvalidContractError):
        ck.valstr("hello", custom=lambda s: s == "world")
