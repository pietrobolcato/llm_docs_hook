"""Sample source code for testing."""

SAMPLE_PYTHON_CODE = {
    "simple_function": "def simple_function():\n    pass",
    "function_with_args": "def function_with_args(param1, param2):\n    return param1 + param2",
    "simple_class": "class TestClass:\n    pass",
    "class_with_methods": """class TestClass:
    def method1(self):
        pass
    def method2(self):
        pass""",
    "private_function": "def _private_function():\n    pass",
    "special_method": "def __str__(self):\n    pass",
    "init_method": "def __init__(self):\n    pass",
    "async_function": "async def async_function():\n    pass",
    "decorated_function": """@decorator1
@decorator2
def decorated_function():
    pass""",
    "function_with_docstring": '''def documented_function():
    """This is a complete docstring."""
    pass''',
    "function_with_incomplete_docstring": '''def incomplete_function(param1):
    """This is incomplete."""
    pass''',
    "function_with_spaces": "def test():\n    pass\n        deeper = True",
    "function_with_tabs": "def test():\n\tpass\n\t\tdeeper = True",
}

SAMPLE_DOCSTRINGS = {
    "simple": "This is a simple docstring.",
    "multi_line": "This is a multi-line docstring.\n\nIt has multiple paragraphs.",
    "google_with_args": """This function does something.

Args:
    param1: Description of param1.
    param2 (int): Description of param2.
    param3 (str, optional): Description of param3.

Returns:
    bool: Description of return value.""",
    "google_with_examples": """This function does something.

Args:
    param1: Description of param1.

Example:
    >>> result = my_function("test")
    >>> print(result)
    True""",
    "google_with_raises": """This function does something.

Args:
    param1: Description of param1.

Raises:
    ValueError: If param1 is invalid.
    TypeError: If param1 is not a string.""",
    "numpy_with_parameters": """This function does something.

Parameters
----------
param1 : str
    Description of param1.
param2 : int
    Description of param2.
param3 : str, optional
    Description of param3.

Returns
-------
bool
    Description of return value.""",
    "numpy_with_examples": """This function does something.

Parameters
----------
param1 : str
    Description of param1.

Examples
--------
>>> result = my_function("test")
>>> print(result)
True""",
    "numpy_with_raises": """This function does something.

Parameters
----------
param1 : str
    Description of param1.

Raises
------
ValueError
    If param1 is invalid.
TypeError
    If param1 is not a string.""",
    "empty": "",
    "whitespace_only": "   \n   \n   ",
}
