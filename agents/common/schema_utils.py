"""Utilities for working with Avro schemas."""

import json
from pathlib import Path
from typing import Dict, Any


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load an Avro schema from the schemas directory.

    Args:
        schema_name: Name of the schema file without extension (e.g., 'deployment-state')

    Returns:
        Parsed schema as a dictionary
    """
    schema_path = Path(__file__).parent.parent / "schemas" / f"{schema_name}.avsc"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        return json.load(f)


def get_schema_string(schema_name: str) -> str:
    """
    Load an Avro schema and return it as a JSON string.

    Args:
        schema_name: Name of the schema file without extension

    Returns:
        Schema as a JSON string
    """
    schema = load_schema(schema_name)
    return json.dumps(schema)


# Available schemas
AVAILABLE_SCHEMAS = [
    "deployment-state",
    "usage-state",
    "metrics-state",
    "current-state"
]
