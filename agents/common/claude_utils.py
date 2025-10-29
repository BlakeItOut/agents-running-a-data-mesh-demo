"""Utilities for interacting with Claude API via Anthropic SDK or AWS Bedrock."""

import json
import os
from typing import Optional, List, Dict, Any

# Anthropic SDK is optional - will check at runtime
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# AWS Bedrock (boto3) is optional
try:
    import boto3
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False


def get_backend():
    """
    Determine which Claude backend to use.

    Returns:
        'bedrock' or 'anthropic'
    """
    backend = os.getenv('CLAUDE_BACKEND', 'anthropic').lower()
    if backend not in ['bedrock', 'anthropic']:
        print(f"Warning: Unknown CLAUDE_BACKEND '{backend}', defaulting to 'anthropic'")
        return 'anthropic'
    return backend


def get_claude_client():
    """
    Get an Anthropic client instance.

    Returns:
        Configured Anthropic client

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set
        ImportError: If anthropic package is not installed
    """
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

    return Anthropic(api_key=api_key)


def get_bedrock_client():
    """
    Get an AWS Bedrock Runtime client instance.

    Supports multiple authentication methods:
    1. BEDROCK_API_KEY environment variable (sets AWS_BEARER_TOKEN_BEDROCK automatically)
    2. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
    3. ~/.aws/credentials file

    Returns:
        Configured boto3 bedrock-runtime client

    Raises:
        ImportError: If boto3 package is not installed
        ValueError: If AWS credentials are not configured
    """
    if not BEDROCK_AVAILABLE:
        raise ImportError("boto3 package not installed. Install with: pip install boto3")

    region = os.getenv('AWS_REGION', 'us-east-1')

    # Check for Bedrock API key and set AWS_BEARER_TOKEN_BEDROCK
    # AWS Bedrock API keys use bearer token authentication
    # The key must include the "bedrock-api-key-" prefix
    bedrock_api_key = os.getenv('BEDROCK_API_KEY')
    if bedrock_api_key:
        os.environ['AWS_BEARER_TOKEN_BEDROCK'] = bedrock_api_key

    # boto3 will automatically use AWS_BEARER_TOKEN_BEDROCK for Bedrock API key auth
    # or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY from env
    # or ~/.aws/credentials
    try:
        client = boto3.client('bedrock-runtime', region_name=region)
        return client
    except Exception as e:
        raise ValueError(f"Failed to create Bedrock client. Ensure AWS credentials are set: {e}")


def call_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 4096,
    temperature: float = 1.0
) -> str:
    """
    Call Claude API with a prompt using either Anthropic API or AWS Bedrock.

    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt to set context
        model: Claude model to use
        max_tokens: Maximum tokens in response
        temperature: Temperature for response generation (0.0-1.0)

    Returns:
        Claude's response as a string
    """
    backend = get_backend()

    if backend == 'bedrock':
        return _call_claude_bedrock(prompt, system_prompt, model, max_tokens, temperature)
    else:
        return _call_claude_anthropic(prompt, system_prompt, model, max_tokens, temperature)


def _call_claude_anthropic(
    prompt: str,
    system_prompt: Optional[str],
    model: str,
    max_tokens: int,
    temperature: float
) -> str:
    """Call Claude via Anthropic API."""
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


def _call_claude_bedrock(
    prompt: str,
    system_prompt: Optional[str],
    model: str,
    max_tokens: int,
    temperature: float
) -> str:
    """Call Claude via AWS Bedrock Runtime."""
    client = get_bedrock_client()

    # Map model names to Bedrock model IDs or inference profiles
    # When using API keys, inference profiles are required (us.anthropic.*)
    # When using IAM credentials, direct model IDs can be used (anthropic.*)

    # Try to detect if we're using API key auth (bearer token) vs IAM
    using_api_key = bool(os.getenv('BEDROCK_API_KEY') or os.getenv('AWS_BEARER_TOKEN_BEDROCK'))

    if using_api_key:
        # Use cross-region inference profiles for API key authentication
        model_id_map = {
            # Claude Sonnet 4.5 (latest)
            "claude-sonnet-4-5-20250929": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            # Claude Sonnet 4
            "claude-sonnet-4-20250514": "us.anthropic.claude-sonnet-4-20250514-v1:0",
            # Claude 3.7 Sonnet
            "claude-3-7-sonnet-20250219": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            # Claude Opus 4.1
            "claude-opus-4-1-20250805": "us.anthropic.claude-opus-4-1-20250805-v1:0",
            # Claude Opus 4
            "claude-opus-4-20250514": "us.anthropic.claude-opus-4-20250514-v1:0",
            # Claude 3.5 Sonnet
            "claude-3-5-sonnet-20250219": "us.anthropic.claude-3-5-sonnet-20250219-v2:0",
            "claude-3-5-sonnet-20241022": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude-3-5-sonnet-20240620": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            # Claude 3.5 Haiku
            "claude-3-5-haiku-20250110": "us.anthropic.claude-3-5-haiku-20250110-v1:0",
            # Claude 3 models
            "claude-3-sonnet-20240229": "us.anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-opus-20240229": "us.anthropic.claude-3-opus-20240229-v1:0",
            "claude-3-haiku-20240307": "us.anthropic.claude-3-haiku-20240307-v1:0",
        }
        default_model = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"  # Latest Sonnet
    else:
        # Use direct model IDs for IAM authentication
        model_id_map = {
            # Claude Sonnet 4.5 (latest)
            "claude-sonnet-4-5-20250929": "anthropic.claude-sonnet-4-5-20250929-v1:0",
            # Claude Sonnet 4
            "claude-sonnet-4-20250514": "anthropic.claude-sonnet-4-20250514-v1:0",
            # Claude 3.7 Sonnet
            "claude-3-7-sonnet-20250219": "anthropic.claude-3-7-sonnet-20250219-v1:0",
            # Claude Opus 4.1
            "claude-opus-4-1-20250805": "anthropic.claude-opus-4-1-20250805-v1:0",
            # Claude Opus 4
            "claude-opus-4-20250514": "anthropic.claude-opus-4-20250514-v1:0",
            # Claude 3.5 Sonnet
            "claude-3-5-sonnet-20250219": "anthropic.claude-3-5-sonnet-20250219-v2:0",
            "claude-3-5-sonnet-20241022": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude-3-5-sonnet-20240620": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            # Claude 3.5 Haiku
            "claude-3-5-haiku-20250110": "anthropic.claude-3-5-haiku-20250110-v1:0",
            # Claude 3 models
            "claude-3-sonnet-20240229": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-opus-20240229": "anthropic.claude-3-opus-20240229-v1:0",
            "claude-3-haiku-20240307": "anthropic.claude-3-haiku-20240307-v1:0",
        }
        default_model = "anthropic.claude-sonnet-4-5-20250929-v1:0"  # Latest Sonnet

    # Use mapped model ID or pass through if already a Bedrock ID
    if model in model_id_map:
        bedrock_model_id = model_id_map[model]
    elif model.startswith("anthropic.") or model.startswith("us.anthropic."):
        bedrock_model_id = model
    else:
        # Default to latest Sonnet
        bedrock_model_id = default_model

    # Construct request body in Anthropic Messages API format
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
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
        request_body["system"] = system_prompt

    # Invoke model
    try:
        response = client.invoke_model(
            modelId=bedrock_model_id,
            body=json.dumps(request_body)
        )

        # Parse response
        response_body = json.loads(response['body'].read())

        # Extract text from response
        if 'content' in response_body and len(response_body['content']) > 0:
            return response_body['content'][0]['text']

        return ""
    except Exception as e:
        raise RuntimeError(f"Failed to invoke Bedrock model: {e}")


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
    # Extract key counts to provide to Claude
    topic_count = len(deployment_data.get("topics", []))
    schema_count = len(deployment_data.get("schemas", []))
    connector_count = len(deployment_data.get("connectors", []))
    domain_count = len(deployment_data.get("domains", {}))
    consumer_groups = usage_data.get("consumer_groups", 0)
    active_consumers = usage_data.get("active_consumers", 0)

    system_prompt = """You are a data platform analyst synthesizing state information.
Your role is to:
1. Analyze deployment, usage, and metrics data
2. Provide a concise 2-3 sentence summary of the current platform state
3. Identify 2-3 notable observations or anomalies

IMPORTANT: Use the KEY STATISTICS provided below for counts. Do not count items yourself as this can lead to errors. Reference these exact numbers in your summary.

Focus on actionable insights and patterns."""

    prompt = f"""Analyze this data platform state and provide a synthesis:

KEY STATISTICS (use these exact numbers - do not recount):
- Total Topics: {topic_count}
- Total Schemas: {schema_count}
- Total Connectors: {connector_count}
- Business Domains: {domain_count}
- Consumer Groups: {consumer_groups}
- Active Consumers: {active_consumers}

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
    Generate a raw idea based on current state (Learning Agent).

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
