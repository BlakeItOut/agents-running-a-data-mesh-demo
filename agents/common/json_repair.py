#!/usr/bin/env python3
"""
JSON Repair Utilities

Attempts to fix common JSON syntax errors that Claude sometimes makes when
generating large, complex JSON structures.
"""

import json
import re
from typing import Any, Optional


def attempt_json_repair(json_str: str) -> Optional[dict]:
    """
    Attempt to repair common JSON syntax errors.

    Tries multiple repair strategies in order:
    1. Parse as-is (maybe it's valid)
    2. Fix missing commas between fields
    3. Fix trailing commas
    4. Fix unescaped quotes in strings
    5. Fix mismatched braces

    Args:
        json_str: The potentially malformed JSON string

    Returns:
        Parsed dict if successful, None if all repair attempts fail
    """
    # Strategy 1: Try parsing as-is
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Fix missing commas between fields
    # Pattern: "field": "value"\n  "nextfield" should be "field": "value",\n  "nextfield"
    repaired = re.sub(
        r'(["\d\}\]true|false|null])\s*\n\s*"',
        r'\1,\n  "',
        json_str
    )
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Fix trailing commas before closing braces/brackets
    repaired = re.sub(r',(\s*[}\]])', r'\1', json_str)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Strategy 4: Combine strategies 2 and 3
    repaired = re.sub(
        r'(["\d\}\]true|false|null])\s*\n\s*"',
        r'\1,\n  "',
        json_str
    )
    repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Strategy 5: Fix common issues with multiline strings
    # If there are unescaped newlines in strings, this is harder to fix automatically
    # Try wrapping with triple quotes conceptually won't work in JSON
    # Skip this for now

    # All repair attempts failed
    return None


def extract_and_repair_json(response_text: str) -> Optional[dict]:
    """
    Extract JSON from various formats and attempt repair.

    Handles:
    - Markdown code blocks (```json or ```)
    - Markdown headers before JSON
    - Trailing content after JSON
    - Common syntax errors

    Args:
        response_text: Raw response from Claude that should contain JSON

    Returns:
        Parsed dict if successful, None otherwise
    """
    response_text = response_text.strip()

    # Step 1: Extract from markdown code blocks
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        if json_end != -1:
            response_text = response_text[json_start:json_end].strip()
    elif response_text.startswith("```") and "```" in response_text[3:]:
        # Generic code block
        json_start = response_text.find("\n") + 1
        json_end = response_text.find("```", json_start)
        if json_end != -1:
            response_text = response_text[json_start:json_end].strip()

    # Step 2: Find first { if response starts with headers
    if not response_text.startswith("{"):
        json_start_idx = response_text.find("{")
        if json_start_idx != -1:
            response_text = response_text[json_start_idx:]

    # Step 3: Find last } to handle trailing content
    if not response_text.endswith("}"):
        json_end_idx = response_text.rfind("}")
        if json_end_idx != -1:
            response_text = response_text[:json_end_idx + 1]

    # Step 4: Attempt to parse/repair
    return attempt_json_repair(response_text)


def safe_json_parse(response: str, fallback: dict = None) -> dict:
    """
    Safely parse JSON response with repair attempts and fallback.

    Args:
        response: Raw response from Claude
        fallback: Dictionary to return if all parsing fails

    Returns:
        Parsed dictionary or fallback dict
    """
    result = extract_and_repair_json(response)
    if result is not None:
        return result

    if fallback is not None:
        return fallback

    # Return minimal error dict
    return {
        "error": "Failed to parse or repair JSON",
        "raw_response_preview": response[:500] if response else ""
    }
