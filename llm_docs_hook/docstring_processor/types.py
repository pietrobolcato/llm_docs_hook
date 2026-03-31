"""Types and enums for docstring processing."""

from enum import Enum


class DocstringStyle(Enum):
    """Supported docstring styles."""

    GOOGLE = "google"
    NUMPY = "numpy"

    @classmethod
    def from_string(cls, style_str: str) -> "DocstringStyle":
        """Create DocstringStyle from string.

        Args:
            style_str (str): The style string (case-insensitive).

        Returns:
            DocstringStyle: The corresponding enum value.

        Raises:
            ValueError: If the style is not supported.
        """
        style_lower = style_str.lower()
        for style in cls:
            if style.value == style_lower:
                return style

        supported_styles = [style.value for style in cls]
        raise ValueError(
            f"Unsupported docstring style: '{style_str}'. "
            f"Supported styles: {supported_styles}"
        )
