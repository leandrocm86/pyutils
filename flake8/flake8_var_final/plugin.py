import ast
from typing import Any, Dict, Generator, Set, Tuple, Type, Optional


class VarFinalChecker:
    name = 'flake8_var_final'
    version = '0.1.0'

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree
        # Track variables by scope to avoid flagging first assignments
        self.vars_by_scope: Dict[Tuple[str, str], Dict[str, int]] = {}
        # Track properties by class to avoid flagging first assignments
        self.all_properties: Dict[str, Set[str]] = {}
        # Current function context
        self.current_class: Optional[str] = None
        self.current_method: Optional[str] = None
        # Current scope identifier (for tracking local variables)
        self.current_scope: Tuple[str, str] = ('', '')

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        # First pass: collect all class properties
        self._collect_all_properties()

        # Second pass: check for reassignments
        for node in self.tree.body:  # type: ignore
            # Track class context
            if isinstance(node, ast.ClassDef):
                old_class = self.current_class
                self.current_class = node.name
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        yield from self._process_function(child)
                self.current_class = old_class
            elif isinstance(node, ast.FunctionDef):
                yield from self._process_function(node)
            else:
                # Process top-level assignments (module scope)
                self.current_scope = ('module', '')
                if isinstance(node, ast.Assign):
                    yield from self._check_assignment(node)
                elif isinstance(node, ast.AugAssign):
                    yield from self._check_aug_assignment(node)

    def _process_function(self, node: ast.FunctionDef) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        """Process a function definition."""
        old_method = self.current_method
        self.current_method = node.name

        # Create a new scope for this function
        if self.current_class:
            self.current_scope = (self.current_class, node.name)
        else:
            self.current_scope = ('function', node.name)

        # Initialize variables for this scope
        if self.current_scope not in self.vars_by_scope:
            self.vars_by_scope[self.current_scope] = {}

        # Find all nested function definitions
        nested_functions = {n for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and n != node}

        # Now, process assignments in the current function's scope,
        # excluding those inside the nested functions we've already handled.
        for child in ast.walk(node):
            is_in_nested = any(nested_func in child.iter_parents() for nested_func in nested_functions)
            if isinstance(child, ast.Assign) and not is_in_nested:
                yield from self._check_assignment(child)
            elif isinstance(child, ast.AugAssign) and not is_in_nested:
                yield from self._check_aug_assignment(child)

        # After processing the current scope, recursively process nested functions
        for nested_func in nested_functions:
            yield from self._process_function(nested_func)

        self.current_method = old_method

    def _collect_all_properties(self) -> None:
        """First pass: collect all properties that are ever assigned in each class."""
        var_current_class = None

        # Add parent pointers to all nodes for easier traversal
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore

        def iter_parents(node: ast.AST):
            while hasattr(node, 'parent'):
                node = node.parent # type: ignore
                yield node
        ast.AST.iter_parents = iter_parents # type: ignore

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                var_current_class = node.name
                self.all_properties[var_current_class] = set()

            if var_current_class and isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                        self.all_properties[var_current_class].add(target.attr)

    def _check_assignment(self, node: ast.Assign) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        """Check a variable or attribute assignment."""
        for target in node.targets:
            # Simple variable assignment: x = value
            if isinstance(target, ast.Name):
                name = target.id
                var_scope_vars = self.vars_by_scope.setdefault(self.current_scope, {})

                if name in var_scope_vars:
                    # This is a reassignment within the same scope
                    if not name.startswith('var_'):
                        yield (
                            node.lineno,
                            node.col_offset,
                            f"VAR001 variable '{name}' reassigned but not prefixed with 'var_'",
                            type(self),
                        )
                else:
                    # First assignment in this scope
                    var_scope_vars[name] = node.lineno

            # Attribute assignment: obj.attr = value
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                obj_name = target.value.id
                attr_name = target.attr

                # Special handling for self.attr assignments
                if obj_name == 'self' and self.current_class:
                    # Allow ANY assignment in __init__ regardless of prefix
                    if self.current_method != '__init__':
                        # Outside __init__, property should have var_ prefix if it's reassigned
                        if attr_name in self.all_properties.get(self.current_class, set()) and not attr_name.startswith('var_'):
                            yield (
                                node.lineno,
                                node.col_offset,
                                f"VAR002 property 'self.{attr_name}' modified outside __init__ but not prefixed with 'var_'",
                                type(self),
                            )
                else:
                    # Regular object property handling
                    # attr_key = (obj_name, attr_name)
                    var_scope_vars = self.vars_by_scope.setdefault(self.current_scope, {})
                    attr_key_str = f"{obj_name}.{attr_name}"

                    if attr_key_str in var_scope_vars:
                        # This is a reassignment within the same scope
                        if not attr_name.startswith('var_'):
                            yield (
                                node.lineno,
                                node.col_offset,
                                f"VAR003 property '{obj_name}.{attr_name}' reassigned but not prefixed with 'var_'",
                                type(self),
                            )
                    else:
                        # First assignment in this scope
                        var_scope_vars[attr_key_str] = node.lineno

    def _check_aug_assignment(self, node: ast.AugAssign) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        """Check an augmented assignment."""
        # Handle variable augmented assignment
        if isinstance(node.target, ast.Name):
            name = node.target.id
            # Augmented assignment is always a modification, so always check
            if not name.startswith('var_'):
                yield (
                    node.lineno,
                    node.col_offset,
                    f"VAR001 variable '{name}' modified with augmented assignment but not prefixed with 'var_'",
                    type(self),
                )

        # Handle attribute augmented assignment
        elif isinstance(node.target, ast.Attribute) and isinstance(node.target.value, ast.Name):
            obj_name = node.target.value.id
            attr_name = node.target.attr

            # Special handling for self.attr assignments with augmented assignment
            if obj_name == 'self' and self.current_class:
                # Even in __init__, augmented assignment implies modifying existing property
                if not attr_name.startswith('var_'):
                    yield (
                        node.lineno,
                        node.col_offset,
                        f"VAR002 property 'self.{attr_name}' modified with augmented assignment but not prefixed with 'var_'",
                        type(self),
                    )
            else:
                # Regular object property handling
                if not attr_name.startswith('var_'):
                    yield (
                        node.lineno,
                        node.col_offset,
                        f"VAR003 property '{obj_name}.{attr_name}' modified with augmented assignment but not prefixed with 'var_'",
                        type(self),
                    )
