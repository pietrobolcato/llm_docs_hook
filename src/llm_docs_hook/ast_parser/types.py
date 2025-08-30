"""Types for the AST parser."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ElementType(Enum):
    """Type of code element."""
    FUNCTION = "function"
    CLASS = "class"

class CodeElement(BaseModel):
    """Represents a code element (function or class) that needs documentation."""
    
    name: str
    element_type: ElementType
    line_number: int
    end_line_number: int
    signature: str
    has_docstring: bool
    docstring_content: Optional[str] = None
    is_incomplete_docstring: bool = False
    is_private: bool = False
    parent_class: Optional[str] = None
    decorators: List[str] = []
    arguments: List[str] = []
    return_annotation: Optional[str] = None