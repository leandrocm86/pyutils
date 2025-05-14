import ast
from typing import Any, Dict, Generator, Set, Tuple, Type, Optional, List

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
        for node in ast.walk(self.tree):
            # Track class context
            if isinstance(node, ast.ClassDef):
                old_class = self.current_class
                self.current_class = node.name
                
                # Process class body
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.FunctionDef):
                        yield from self._process_function(child)
                
                self.current_class = old_class
            
            # Process top-level functions
            elif isinstance(node, ast.FunctionDef) and self.current_class is None:
                yield from self._process_function(node)
            
            # Process top-level assignments (module scope)
            elif self.current_class is None and self.current_method is None:
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
        
        # Process function body
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                yield from self._check_assignment(child)
            elif isinstance(child, ast.AugAssign):
                yield from self._check_aug_assignment(child)
            elif isinstance(child, (ast.For, ast.While, ast.If, ast.With)):
                # Process block statements recursively
                for block_child in ast.iter_child_nodes(child):
                    if isinstance(block_child, ast.Assign):
                        yield from self._check_assignment(block_child)
                    elif isinstance(block_child, ast.AugAssign):
                        yield from self._check_aug_assignment(block_child)
        
        self.current_method = old_method
    
    def _collect_all_properties(self) -> None:
        """First pass: collect all properties that are ever assigned in each class."""
        current_class = None
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                current_class = node.name
                self.all_properties[current_class] = set()
            
            if current_class and isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                        self.all_properties[current_class].add(target.attr)
    
    def _check_assignment(self, node: ast.Assign) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        """Check a variable or attribute assignment."""
        for target in node.targets:
            # Simple variable assignment: x = value
            if isinstance(target, ast.Name):
                name = target.id
                scope_vars = self.vars_by_scope.setdefault(self.current_scope, {})
                
                if name in scope_vars:
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
                    scope_vars[name] = node.lineno
            
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
                    attr_key = (obj_name, attr_name)
                    scope_vars = self.vars_by_scope.setdefault(self.current_scope, {})
                    attr_key_str = f"{obj_name}.{attr_name}"
                    
                    if attr_key_str in scope_vars:
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
                        scope_vars[attr_key_str] = node.lineno
    
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