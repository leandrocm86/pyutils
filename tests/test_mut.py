import pytest
from utils.mut import InvalidMutationError, mut


class Person:
    def __init__(self, name: str, age: int, nicknames: tuple[str, ...] = tuple()):
        self.name = name
        self.age = age
        self.nicknames = nicknames
        self.friends: list[Person] = []


def test_mut_immutable():
    person = Person('John', 30)
    with pytest.raises(AssertionError):
        with mut(person.age):
            person.age = 31
    assert person.age == 30


def test_mut_no_expectations():
    person = Person('John', 30)
    with mut(person):
        person.age = 31
    assert person.age == 31


def test_mut_expect_success():
    person = Person('John', 30)
    with mut(person, expect=lambda p: p.age == 31):
        person.age = 31
    assert person.age == 31

    person = Person('John', 30)
    with mut(person, expect=lambda p: len(p.nicknames) == 2):
        person.nicknames = ('Nick1', 'Nick2')
    assert person.nicknames == ('Nick1', 'Nick2')


def test_mut_expect_fail():
    person = Person('John', 30)
    with pytest.raises(InvalidMutationError):
        with mut(person, expect=lambda p: p.age == 31):
            person.age = 30

    person = Person('John', 30)
    with pytest.raises(InvalidMutationError):  # IndexError
        with mut(person, expect=lambda p: p.nicknames[0] == 'Joe'):
            person.age = 31


def test_mut_expect_diff_success():
    person = Person('John', 30)
    with mut(person, expect_diff=lambda p1, p2: p1.age < p2.age):
        person.age += 1
    assert person.age == 31

    person = Person('John', 30, ('Nick1', 'Nick2'))
    with mut(person, expect_diff=lambda p1, p2: p1.nicknames[0] != p2.nicknames[0]):
        person.nicknames = ('Nick2', 'Nick1')
    assert person.nicknames == ('Nick2', 'Nick1')


def test_mut_expect_diff_fail():
    person = Person('John', 30)
    person.friends = [Person('Friend1', 20), Person('Friend2', 21)]

    # Since the list of friends is a shallow copy, the original list is not preserved
    with pytest.raises(InvalidMutationError):
        with mut(person, expect_diff=lambda p1, p2: p1.friends[0].age != p2.friends[0].age):
            person.friends[0].age += 1
    assert person.friends[0].age == 21

    person = Person('John', 30)
    with pytest.raises(InvalidMutationError):  # IndexError
        with mut(person, expect_diff=lambda p1, p2: p1.nicknames[0] != p2.nicknames[0]):
            person.nicknames = ('Nick2', 'Nick1')
    assert person.nicknames == ('Nick2', 'Nick1')

    person = Person('John', 30)
    with pytest.raises(InvalidMutationError):
        with mut(person, expect_diff=lambda p1, p2: p1.age == p2.age - 1):
            person.age += 1
            person.age += 1
    assert person.age == 32


def test_mut_expect_deepdiff_success():
    person = Person('John', 30)
    person.friends = [Person('Friend1', 20), Person('Friend2', 21)]
    with mut(person, expect_deepdiff=lambda p1, p2: p1.friends[0].age != p2.friends[0].age):
        person.friends[0].age += 1
    assert person.friends[0].age == 21


def test_mut_expect_deepdiff_fail():
    person = Person('John', 30)
    person.friends = [Person('Friend1', 20), Person('Friend2', 21)]
    with pytest.raises(InvalidMutationError):
        with mut(person, expect_deepdiff=lambda p1, p2: p1.friends[0].age == p2.friends[0].age):
            person.friends[0].age += 1
    assert person.friends[0].age == 21
