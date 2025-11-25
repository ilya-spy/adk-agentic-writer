"""Utilities for generating JSON schemas for LLM prompts."""

import json
from typing import Any, Dict, Type

from pydantic import BaseModel


def model_to_example_json(model: Type[BaseModel], indent: int = 2) -> str:
    """
    Generate a simplified example JSON from a Pydantic model schema.
    More human-readable than full JSON schema for prompts.

    Args:
        model: The Pydantic model class
        indent: Indentation level for JSON formatting

    Returns:
        Simplified example JSON string with inline descriptions
    """
    schema = model.model_json_schema()

    def schema_to_example(schema_dict: dict, definitions: dict) -> Any:
        """Convert JSON schema to example JSON with descriptions."""
        properties = schema_dict.get("properties", {})
        required = schema_dict.get("required", [])
        example = {}

        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type")
            description = prop_schema.get("description", "")
            default = prop_schema.get("default")
            enum_values = prop_schema.get("enum")

            # Handle references
            if "$ref" in prop_schema:
                ref_path = prop_schema["$ref"].split("/")[-1]
                if ref_path in definitions:
                    example[prop_name] = schema_to_example(
                        definitions[ref_path], definitions
                    )
                continue

            # Handle anyOf (for Optional types)
            if "anyOf" in prop_schema:
                # Find the non-null type
                for any_of_schema in prop_schema["anyOf"]:
                    if any_of_schema.get("type") != "null":
                        prop_schema = {**prop_schema, **any_of_schema}
                        prop_type = prop_schema.get("type")
                        break

            # Build example based on type
            if prop_type == "string":
                if enum_values:
                    example[prop_name] = "|".join(enum_values)
                else:
                    example[prop_name] = (
                        f"string - {description}" if description else "string"
                    )
            elif prop_type == "integer":
                example[prop_name] = default if default is not None else 0
            elif prop_type == "number":
                example[prop_name] = default if default is not None else 0.0
            elif prop_type == "boolean":
                example[prop_name] = default if default is not None else False
            elif prop_type == "array":
                items_schema = prop_schema.get("items", {})
                if "$ref" in items_schema:
                    ref_path = items_schema["$ref"].split("/")[-1]
                    if ref_path in definitions:
                        example[prop_name] = [
                            schema_to_example(definitions[ref_path], definitions)
                        ]
                else:
                    item_type = items_schema.get("type", "string")
                    item_desc = items_schema.get("description", description)
                    if item_type == "string":
                        example[prop_name] = (
                            [f"string - {item_desc}"] if item_desc else ["string"]
                        )
                    elif item_type == "integer":
                        example[prop_name] = [0]
                    elif item_type == "number":
                        example[prop_name] = [0.0]
                    else:
                        example[prop_name] = []
            elif prop_type == "object":
                if "additionalProperties" in prop_schema:
                    example[prop_name] = {}
                elif "properties" in prop_schema:
                    example[prop_name] = schema_to_example(prop_schema, definitions)
                else:
                    example[prop_name] = {}
            elif prop_type is None and default is not None:
                example[prop_name] = default
            else:
                # For optional fields without default
                example[prop_name] = None

        return example

    definitions = schema.get("$defs", {})
    example = schema_to_example(schema, definitions)
    return json.dumps(example, indent=indent)


def model_to_json_schema(model: Type[BaseModel], indent: int = 2) -> str:
    """
    Generate a full JSON schema from a Pydantic model.

    Args:
        model: The Pydantic model class
        indent: Indentation level for JSON formatting

    Returns:
        Full JSON schema string
    """
    schema = model.model_json_schema()
    return json.dumps(schema, indent=indent)


def build_schema_instruction(model: Type[BaseModel]) -> str:
    """
    Build an output format instruction section with JSON schema.

    Args:
        model: The Pydantic model class

    Returns:
        Formatted instruction text with schema
    """
    schema_json = model_to_example_json(model)
    return f"""
Output Format:
You must generate your output as a valid JSON object matching the {model.__name__} schema:

{schema_json}"""
