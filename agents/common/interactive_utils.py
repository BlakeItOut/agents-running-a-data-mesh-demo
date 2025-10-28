#!/usr/bin/env python3
"""
Interactive utilities for human-in-the-loop agent workflows.

Provides structured prompts with clear formatting for better user experience.
"""

from typing import List, Dict, Optional, Any


def print_section_header(title: str, width: int = 80):
    """Print a formatted section header."""
    print(f"\n{'=' * width}")
    print(title.center(width))
    print('=' * width)


def print_subsection(title: str, width: int = 80):
    """Print a formatted subsection divider."""
    print(f"\n{'─' * width}")
    print(title)
    print('─' * width)


def ask_choice(
    prompt: str,
    choices: Dict[str, str],
    allow_invalid: bool = False
) -> str:
    """
    Ask user to select from a set of choices.

    Args:
        prompt: The question to ask
        choices: Dict of choice_key -> description
        allow_invalid: If True, accepts any input (for text entry)

    Returns:
        Selected choice key
    """
    print(f"\n{prompt}")
    print()

    # Display choices
    for key, description in choices.items():
        print(f"  [{key}] {description}")

    print()

    valid_choices = list(choices.keys())

    while True:
        try:
            response = input("Your choice: ").strip().lower()

            if allow_invalid or response in valid_choices:
                return response

            print(f"Invalid choice. Please enter one of: {', '.join(valid_choices)}")

        except (KeyboardInterrupt, EOFError):
            print("\n\nInterrupted by user")
            raise


def ask_text(
    prompt: str,
    default: Optional[str] = None,
    allow_empty: bool = True
) -> str:
    """
    Ask user for text input.

    Args:
        prompt: The question/field name to ask
        default: Default value to use if user presses Enter
        allow_empty: If False, will keep prompting until non-empty input

    Returns:
        User's text input
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    while True:
        try:
            response = input(full_prompt).strip()

            # Use default if provided and user entered nothing
            if not response and default:
                return default

            # Check if empty input is allowed
            if not response and not allow_empty:
                print("This field cannot be empty. Please enter a value.")
                continue

            return response

        except (KeyboardInterrupt, EOFError):
            print("\n\nInterrupted by user")
            raise


def ask_yes_no(prompt: str, default: Optional[bool] = None) -> bool:
    """
    Ask a yes/no question.

    Args:
        prompt: The question to ask
        default: Default value (True for Yes, False for No, None for no default)

    Returns:
        True for yes, False for no
    """
    if default is True:
        suffix = " [Y/n]: "
    elif default is False:
        suffix = " [y/N]: "
    else:
        suffix = " [y/n]: "

    while True:
        try:
            response = input(f"{prompt}{suffix}").strip().lower()

            if not response and default is not None:
                return default

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")

        except (KeyboardInterrupt, EOFError):
            print("\n\nInterrupted by user")
            raise


def ask_multiline(prompt: str, end_marker: str = "END") -> str:
    """
    Ask for multi-line text input.

    Args:
        prompt: The question to ask
        end_marker: String to type to end input (case-insensitive)

    Returns:
        Multi-line text input
    """
    print(f"\n{prompt}")
    print(f"(Type '{end_marker}' on a new line when done)")
    print()

    lines = []

    try:
        while True:
            line = input()
            if line.strip().upper() == end_marker.upper():
                break
            lines.append(line)

        return '\n'.join(lines)

    except (KeyboardInterrupt, EOFError):
        print("\n\nInterrupted by user")
        raise


def confirm_action(action_description: str, default: bool = False) -> bool:
    """
    Ask user to confirm an action before proceeding.

    Args:
        action_description: Description of the action to confirm
        default: Default choice

    Returns:
        True if user confirmed, False otherwise
    """
    print(f"\n⚠️  {action_description}")
    return ask_yes_no("Are you sure you want to proceed?", default=default)


def display_item_summary(
    item: Dict[str, Any],
    title: str,
    fields: List[tuple[str, str]],
    width: int = 80
):
    """
    Display a formatted summary of an item.

    Args:
        item: The item dictionary to display
        title: Title for the summary
        fields: List of (label, field_key) tuples to display
        width: Width of the display
    """
    print_section_header(title, width=width)

    for label, field_key in fields:
        value = item.get(field_key, 'N/A')

        # Handle different value types
        if isinstance(value, list):
            print(f"\n{label} ({len(value)}):")
            for i, v in enumerate(value, 1):
                if isinstance(v, dict):
                    # For dict items, show a compact representation
                    print(f"   {i}. {v}")
                else:
                    print(f"   {i}. {v}")
        elif isinstance(value, dict):
            print(f"\n{label}:")
            for k, v in value.items():
                print(f"   {k}: {v}")
        elif isinstance(value, float):
            print(f"{label}: {value:.2f}")
        else:
            print(f"{label}: {value}")


def pause_for_user(message: str = "Press Enter to continue..."):
    """
    Pause execution and wait for user to press Enter.

    Args:
        message: Message to display to user
    """
    try:
        input(f"\n{message}")
    except (KeyboardInterrupt, EOFError):
        print("\n\nInterrupted by user")
        raise


def print_success(message: str):
    """Print a success message."""
    print(f"\n✅ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"\n❌ {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"\n⚠️  {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"\n📋 {message}")
