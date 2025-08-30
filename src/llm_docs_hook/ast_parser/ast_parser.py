"""AST parsing utilities for detecting functions and classes without docstrings."""

import ast
from pathlib import Path
from typing import List, Optional, Set, Union

from src.llm_docs_hook.ast_parser.types import CodeElement, ElementType


class PythonASTParser:
    """Parser for Python AST to find functions and classes without docstrings."""

    def __init__(self, include_private: bool = False, update_incomplete: bool = False):
        """Initialize the AST parser.

        Args:
            include_private (bool): Whether to include private methods/functions.
                Optional, defaults to False.
            update_incomplete (bool): Whether to update incomplete docstrings.
                Optional, defaults to False.
        """
        self.include_private = include_private
        self.update_incomplete = update_incomplete
        self.current_class = None

    def parse_file(self, file_path: Union[str, Path]) -> List[CodeElement]:
        """Parse a Python file and extract functions/classes without docstrings.

        Args:
            file_path (Union[str, Path]): Path to the Python file to parse.

        Returns:
            List[CodeElement]: List of code elements that need docstrings.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            SyntaxError: If the file contains invalid Python syntax.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                source_code = file.read()
            
            tree = ast.parse(source_code)
            return self._extract_elements(tree, source_code)
            
        except SyntaxError as error:
            raise SyntaxError(f"Invalid Python syntax in {file_path}: {error}") from error

    def _extract_elements(self, tree: ast.AST, source_code: str) -> List[CodeElement]:
        """Extract functions and classes from the AST.

        Args:
            tree (ast.AST): The parsed AST tree.
            source_code (str): The original source code.

        Returns:
            List[CodeElement]: List of code elements found in the AST.
        """
        elements = []
        source_lines = source_code.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                element = self._create_code_element(node, source_lines)
                if element and self._should_include_element(element):
                    elements.append(element)
        
        return elements

    def _create_code_element(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], 
                           source_lines: List[str]) -> Optional[CodeElement]:
        """Create a CodeElement from an AST node.

        Args:
            node (Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]): The AST node.
            source_lines (List[str]): Lines of the source code.

        Returns:
            Optional[CodeElement]: Created CodeElement or None if it should be skipped.
        """
        name = node.name
        is_private = name.startswith('_') and not (name.startswith('__') and name.endswith('__'))
        
        # Skip private elements if not including them (but allow special methods like __init__)
        if is_private and not self.include_private:
            return None

        # Determine element type
        if isinstance(node, ast.ClassDef):
            element_type = ElementType.CLASS

            # Track current class for nested functions
            old_class = self.current_class
            self.current_class = name
        else:
            element_type = ElementType.FUNCTION

        # Check if element has docstring and get its content
        has_docstring = self._has_docstring(node)
        docstring_content = self._get_docstring_content(node) if has_docstring else None
        is_incomplete_docstring = self._is_incomplete_docstring(docstring_content, node) if has_docstring else False
        
        # Get decorators
        decorators = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
        # Get signature
        signature = self._get_signature(node, source_lines)
        
        # Get arguments and return annotation for functions
        arguments = []
        return_annotation = None

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = self._get_arguments(node)
            return_annotation = self._get_return_annotation(node)

        element = CodeElement(
            name=name,
            element_type=element_type,
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
            signature=signature,
            has_docstring=has_docstring,
            docstring_content=docstring_content,
            is_incomplete_docstring=is_incomplete_docstring,
            is_private=is_private,
            parent_class=self.current_class if element_type == ElementType.FUNCTION else None,
            decorators=decorators,
            arguments=arguments,
            return_annotation=return_annotation,
        )

        # Restore class context
        if isinstance(node, ast.ClassDef):
            self.current_class = old_class

        return element

    def _should_include_element(self, element: CodeElement) -> bool:
        """Determine if an element should be included in the results.

        Args:
            element (CodeElement): The code element to check.

        Returns:
            bool: True if the element should be included, False otherwise.
        """
        # Include if no docstring at all
        if not element.has_docstring:
            pass  # Continue with other checks

        # Include if has incomplete docstring and we're updating incomplete ones
        elif element.is_incomplete_docstring and self.update_incomplete:
            pass  # Continue with other checks
        
        # Skip if has complete docstring
        else:
            return False
            
        # Skip private elements if not including them
        if element.is_private and not self.include_private:
            return False
            
        # Skip special methods except __init__
        if (element.name.startswith('__') and element.name.endswith('__') 
            and element.name != '__init__'):
            return False
            
        return True

    def _has_docstring(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> bool:
        """Check if a node has a docstring.

        Args:
            node (Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]): The AST node to check.

        Returns:
            bool: True if the node has a docstring, False otherwise.
        """
        if not node.body:
            return False
            
        first_statement = node.body[0]
        
        # Check if first statement is a string literal (docstring)
        if isinstance(first_statement, ast.Expr):
            if isinstance(first_statement.value, ast.Constant):
                return isinstance(first_statement.value.value, str)
            elif isinstance(first_statement.value, ast.Str):  # Python < 3.8 compatibility
                return True
                
        return False

    def _get_docstring_content(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> Optional[str]:
        """Extract the docstring content from a node.

        Args:
            node (Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]): The AST node.

        Returns:
            Optional[str]: The docstring content if present, None otherwise.
        """
        if not node.body:
            return None
            
        first_statement = node.body[0]
        
        # Check if first statement is a string literal (docstring)
        if isinstance(first_statement, ast.Expr):
            if isinstance(first_statement.value, ast.Constant):
                if isinstance(first_statement.value.value, str):
                    return first_statement.value.value
            elif isinstance(first_statement.value, ast.Str):  # Python < 3.8 compatibility
                return first_statement.value.s
                
        return None

    def _is_incomplete_docstring(self, docstring_content: Optional[str], 
                                node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> bool:
        """Check if a docstring is incomplete (missing Args, Returns, etc.).

        Args:
            docstring_content (Optional[str]): The docstring content to check.
            node (Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]): The AST node.

        Returns:
            bool: True if the docstring is incomplete, False otherwise.
        """
        if not docstring_content:
            return False
            
        # For functions, check if it has arguments but no Args section
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Get function arguments (excluding 'self' for methods)
            args = self._get_arguments(node)
            if node.name != '__init__' and args and args[0] == 'self':
                args = args[1:]  # Remove 'self' for methods
            elif node.name == '__init__' and args and args[0] == 'self':
                args = args[1:]  # Remove 'self' for __init__
                
            # Check if function has arguments but docstring lacks Args section
            if args and 'Args:' not in docstring_content and 'Arguments:' not in docstring_content:
                return True
                
            # Check if function has return annotation but no Returns section
            if (node.returns and 
                'Returns:' not in docstring_content and 
                'Return:' not in docstring_content and
                node.name != '__init__'):  # __init__ doesn't need Returns section
                return True
        
        # For classes, check if it has __init__ arguments but no Args section
        elif isinstance(node, ast.ClassDef):
            # Find __init__ method
            init_method = None
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == '__init__':
                    init_method = child
                    break
                    
            if init_method:
                init_args = self._get_arguments(init_method)
                if init_args and init_args[0] == 'self':
                    init_args = init_args[1:]  # Remove 'self'
                    
                if init_args and 'Args:' not in docstring_content and 'Arguments:' not in docstring_content:
                    return True
        
        return False

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get the name of a decorator.

        Args:
            decorator (ast.expr): The decorator AST node.

        Returns:
            str: The decorator name.
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._get_attribute_name(decorator)
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return str(decorator)

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get the full name of an attribute access.

        Args:
            node (ast.Attribute): The attribute AST node.

        Returns:
            str: The full attribute name.
        """
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        else:
            return node.attr

    def _get_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], 
                      source_lines: List[str]) -> str:
        """Extract the signature of a function or class from source lines.

        Args:
            node (Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]): The AST node.
            source_lines (List[str]): Lines of the source code.

        Returns:
            str: The signature string.
        """
        start_line = node.lineno - 1  # Convert to 0-based indexing
        
        # Find the line with the colon
        signature_lines = []
        for index in range(start_line, min(len(source_lines), start_line + 10)):  # Look ahead max 10 lines
            line = source_lines[index].strip()
            signature_lines.append(line)
            if ':' in line:
                break
        
        return ' '.join(signature_lines)

    def _get_arguments(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Get argument names from a function node.

        Args:
            node (Union[ast.FunctionDef, ast.AsyncFunctionDef]): The function AST node.

        Returns:
            List[str]: List of argument names.
        """
        arguments = []
        
        # Regular arguments
        for arg in node.args.args:
            arguments.append(arg.arg)
            
        # Varargs (*args)
        if node.args.vararg:
            arguments.append(f"*{node.args.vararg.arg}")
            
        # Keyword arguments (**kwargs)
        if node.args.kwarg:
            arguments.append(f"**{node.args.kwarg.arg}")
            
        return arguments

    def _get_return_annotation(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]:
        """Get the return type annotation from a function node.

        Args:
            node (Union[ast.FunctionDef, ast.AsyncFunctionDef]): The function AST node.

        Returns:
            Optional[str]: The return type annotation if present, None otherwise.
        """
        if node.returns:
            return ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        return None


