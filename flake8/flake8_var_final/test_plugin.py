import ast
from typing import Set
from flake8_var_final.plugin import VarFinalChecker


def _run_checker(code: str) -> Set[str]:
    """
    Helper function to run the checker on a given code string
    and return a set of formatted error messages.
    """
    tree = ast.parse(code)
    checker = VarFinalChecker(tree)
    errors = checker.run()
    return {f"{line}:{col} {msg}" for line, col, msg, _ in errors}


def test_no_errors_for_final_variables():
    """
    Tests that code with variables that are assigned only once does not
    produce any errors.
    """
    code = """
x = 10
y = 20

def my_func():
    a = 1
    b = 2
"""
    errors = _run_checker(code)
    assert not errors


def test_bug_fix_same_variable_name_in_different_scopes():
    """
    Tests the fix for the bug where variables with the same name in different
    functions were incorrectly flagged. This should produce no errors.
    """
    code = """
def func_one():
    my_var = 100  # First assignment in this scope

def func_two():
    my_var = 200  # First assignment in this scope, should not be a reassignment
"""
    errors = _run_checker(code)
    assert not errors, "Should not flag variables with the same name in different function scopes."


def test_reassignment_of_simple_variable():
    """
    Tests that reassigning a variable not prefixed with 'var_' is flagged.
    """
    code = """
x = 10
x = 20  # Reassignment
"""
    errors = _run_checker(code)
    assert len(errors) == 1
    assert "3:0 VAR001 variable 'x' reassigned but not prefixed with 'var_'" in errors


def test_valid_reassignment_with_var_prefix():
    """
    Tests that reassigning a variable prefixed with 'var_' is allowed.
    """
    code = """
var_x = 10
var_x = 20
"""
    errors = _run_checker(code)
    assert not errors


def test_augmented_assignment_error():
    """
    Tests that augmented assignment on a non-prefixed variable is flagged.
    """
    code = """
x = 10
x += 5
"""
    errors = _run_checker(code)
    assert len(errors) == 1
    assert "3:0 VAR001 variable 'x' modified with augmented assignment but not prefixed with 'var_'" in errors


def test_valid_augmented_assignment_with_var_prefix():
    """
    Tests that augmented assignment on a prefixed variable is allowed.
    """
    code = """
var_x = 10
var_x += 5
"""
    errors = _run_checker(code)
    assert not errors


def test_class_property_modification_outside_init():
    """
    Tests that modifying a property outside __init__ is flagged if not prefixed.
    """
    code = """
class MyClass:
    def __init__(self):
        self.prop = 1

    def update_prop(self):
        self.prop = 2  # Error: modified outside __init__
"""
    errors = _run_checker(code)
    assert len(errors) == 1
    assert "7:8 VAR002 property 'self.prop' modified outside __init__ but not prefixed with 'var_'" in errors


def test_valid_class_property_modification_with_var_prefix():
    """
    Tests that modifying a 'var_' prefixed property outside __init__ is allowed.
    """
    code = """
class MyClass:
    def __init__(self):
        self.var_prop = 1

    def update_prop(self):
        self.var_prop = 2
"""
    errors = _run_checker(code)
    assert not errors


def test_object_attribute_reassignment():
    """
    Tests that reassigning an attribute on a regular object is flagged.
    """
    code = """
class Data:
    pass

d = Data()
d.value = 100
d.value = 200  # Reassignment
"""
    errors = _run_checker(code)
    assert len(errors) == 1
    assert "7:0 VAR003 property 'd.value' reassigned but not prefixed with 'var_'" in errors


def test_valid_assignment_with_same_variable_name_from_nested_function():
    """
    Tests that it's ok to have variables with the same name in and out nested functions being assigned.
    """
    code = """
def outer_func():
    x = a
    def inner_func():
        x = b
"""
    errors = _run_checker(code)
    assert not errors


def test_nested_function_inside_loop_with_same_variable_names():
    """
    Tests that variables in a nested function defined inside a loop
    do not conflict with variables in the outer function's scope.
    This covers the complex scenario found in style.py.
    """
    code = """
def outer_func():
    x = 1  # Outer scope 'x'

    for i in range(1):
        line_width = 100  # Outer scope 'line_width' (within loop)

        def inner_func():
            x = 2  # Inner scope 'x', should not conflict
            line_width = 50  # Inner scope 'line_width', should not conflict

        inner_func()
"""
    errors = _run_checker(code)
    assert not errors, f"False positives found: {errors}"
