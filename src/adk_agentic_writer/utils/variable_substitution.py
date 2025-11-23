"""Variable substitution utilities for task prompt formatting.

Coordinators can use {variable} syntax in task prompts to inject values
from the agent's runtime variable storage.
"""

import re
from typing import Any, Dict


def substitute_variables(text: str, variables: Dict[str, Any]) -> str:
    """
    Substitute variables in text using {variable} syntax.

    Args:
        text: Text containing {variable} placeholders
        variables: Dictionary of variable name to value mappings

    Returns:
        Text with variables substituted

    Examples:
        >>> variables = {"topic": "Python", "difficulty": "medium"}
        >>> substitute_variables("Create a {difficulty} quiz about {topic}", variables)
        'Create a medium quiz about Python'

        >>> variables = {"count": 5, "type": "questions"}
        >>> substitute_variables("Generate {count} {type}", variables)
        'Generate 5 questions'
    """
    # Pattern to find {variable} placeholders
    pattern = r"\{([^}]+)\}"

    def replace_var(match):
        var_name = match.group(1)
        # Support nested dictionary access with dot notation
        # e.g., {config.max_items}
        if "." in var_name:
            parts = var_name.split(".")
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, match.group(0))
                else:
                    return match.group(0)  # Return original if can't access
            return str(value)
        else:
            # Simple variable lookup
            value = variables.get(var_name, match.group(0))
            return str(value) if value != match.group(0) else match.group(0)

    return re.sub(pattern, replace_var, text)


def extract_variable_names(text: str) -> list[str]:
    """
    Extract variable names from text containing {variable} placeholders.

    Args:
        text: Text containing {variable} placeholders

    Returns:
        List of variable names found in text

    Examples:
        >>> extract_variable_names("Create a {difficulty} quiz about {topic}")
        ['difficulty', 'topic']
    """
    pattern = r"\{([^}]+)\}"
    return re.findall(pattern, text)


def validate_variables(text: str, variables: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate that all required variables are present.

    Args:
        text: Text containing {variable} placeholders
        variables: Dictionary of variable name to value mappings

    Returns:
        Tuple of (is_valid, missing_variables)

    Examples:
        >>> variables = {"topic": "Python"}
        >>> validate_variables("Create a {difficulty} quiz about {topic}", variables)
        (False, ['difficulty'])

        >>> variables = {"topic": "Python", "difficulty": "medium"}
        >>> validate_variables("Create a {difficulty} quiz about {topic}", variables)
        (True, [])
    """
    required_vars = extract_variable_names(text)
    missing = []

    for var_name in required_vars:
        # Support nested access
        if "." in var_name:
            parts = var_name.split(".")
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        missing.append(var_name)
                        break
                else:
                    missing.append(var_name)
                    break
        else:
            if var_name not in variables:
                missing.append(var_name)

    return (len(missing) == 0, missing)
