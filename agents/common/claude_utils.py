"""Utilities for interacting with Claude API via Anthropic SDK."""

import os
from typing import Optional, List, Dict, Any
from anthropic import Anthropic


def get_claude_client() -> Anthropic:
    """
    Get an Anthropic client instance.

    Returns:
        Configured Anthropic client

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

    return Anthropic(api_key=api_key)


def call_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 4096,
    temperature: float = 1.0
) -> str:
    """
    Call Claude API with a prompt.

    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt to set context
        model: Claude model to use
        max_tokens: Maximum tokens in response
        temperature: Temperature for response generation (0.0-1.0)

    Returns:
        Claude's response as a string
    """
    client = get_claude_client()

    message_params = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    if system_prompt:
        message_params["system"] = system_prompt

    response = client.messages.create(**message_params)

    # Extract text from response
    if response.content and len(response.content) > 0:
        return response.content[0].text

    return ""


def synthesize_state(
    deployment_data: Dict[str, Any],
    usage_data: Dict[str, Any],
    metrics_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use Claude to synthesize three state inputs into a coherent summary.

    Args:
        deployment_data: Deployment state data
        usage_data: Usage state data
        metrics_data: Metrics state data

    Returns:
        Dictionary with 'summary' and 'observations' keys
    """
    system_prompt = """You are a data platform analyst synthesizing state information.
Your role is to:
1. Analyze deployment, usage, and metrics data
2. Provide a concise 2-3 sentence summary of the current platform state
3. Identify 2-3 notable observations or anomalies

Focus on actionable insights and patterns."""

    prompt = f"""Analyze this data platform state and provide a synthesis:

DEPLOYMENT STATE:
{format_json(deployment_data)}

USAGE STATE:
{format_json(usage_data)}

METRICS STATE:
{format_json(metrics_data)}

Provide your response in this exact JSON format:
{{
  "summary": "2-3 sentence summary of platform state",
  "observations": ["observation 1", "observation 2", "observation 3"]
}}
"""

    response = call_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.3  # Lower temperature for more consistent output
    )

    # Parse JSON response
    import json
    try:
        # Try to extract JSON from response
        # Claude sometimes wraps JSON in markdown code blocks
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Failed to parse Claude response as JSON: {e}")
        print(f"Response: {response}")
        # Return a default structure
        return {
            "summary": response[:500],  # First 500 chars
            "observations": []
        }


def format_json(data: Dict[str, Any]) -> str:
    """Format dictionary as readable JSON string."""
    import json
    return json.dumps(data, indent=2)


def generate_idea(current_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a raw idea based on current state (Learning Prompt).

    Args:
        current_state: Current platform state

    Returns:
        Dictionary with idea details
    """
    system_prompt = """You are an innovation agent for a data platform.
Your role is to analyze the current state and propose improvements or new data products.
Be creative but practical. Focus on value-add opportunities."""

    prompt = f"""Based on this current platform state, propose ONE new idea:

CURRENT STATE:
{format_json(current_state)}

Generate an idea for:
- A new data product to build
- An improvement to existing infrastructure
- A process optimization
- A governance enhancement

Provide your response in this JSON format:
{{
  "title": "Brief title for the idea",
  "description": "Detailed description (2-3 sentences)",
  "rationale": "Why this idea is valuable",
  "category": "data_product|infrastructure|process|governance"
}}
"""

    response = call_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.7  # Higher temperature for creativity
    )

    # Parse response
    import json
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Failed to parse idea response: {e}")
        return {
            "title": "Generated Idea",
            "description": response[:300],
            "rationale": "Unknown",
            "category": "other"
        }
