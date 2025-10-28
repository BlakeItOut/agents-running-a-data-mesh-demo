#!/usr/bin/env python3
"""
Scope Agent - Evaluation Layer

Analyzes approved data product ideas for:
- Technical complexity and scope
- Integration points and dependencies
- Scope creep risks
- Recommended scope adjustments

Consumes refined/approved ideas and publishes scope challenges.
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, UTC
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.kafka_utils import (
    create_avro_consumer,
    create_avro_producer,
    consume_latest_message,
    produce_message
)
from common.schema_utils import get_schema_string
from common.claude_utils import call_claude


def load_approved_ideas_from_kafka(limit_one=False):
    """Load approved ideas from Kafka topic."""
    print("\n1. Loading approved ideas from Kafka...")

    schema_str = get_schema_string("raw-ideas")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"scope-agent-{datetime.now().timestamp()}"  # Unique group to read all messages
    )

    consumer.subscribe(["agent-state-raw-ideas"])

    ideas = []
    try:
        timeout_ms = 5000
        while True:
            msg = consumer.poll(timeout=timeout_ms / 1000.0)

            if msg is None:
                break

            if msg.error():
                continue

            value = deserializer(msg.value(), None)
            if value and value.get("status") == "APPROVED":
                ideas.append(value)

    finally:
        consumer.close()

    # Sort by timestamp (most recent first) if ideas have timestamps
    if ideas and 'timestamp' in ideas[0]:
        ideas.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # In demo mode, only process the most recent approved idea
    if limit_one and ideas:
        ideas = [ideas[0]]
        print(f"   ✅ Loaded latest approved idea: {ideas[0].get('title')}")
    else:
        print(f"   ✅ Loaded {len(ideas)} approved idea{'s' if len(ideas) != 1 else ''}")

    return ideas


def load_approved_ideas_from_files(limit_one=False):
    """Load approved ideas from dry-run output files."""
    print("\n1. Loading approved ideas from dry-run output...")

    output_dir = Path(__file__).parent.parent / "dry-run-output"
    ideas = []

    # Find all raw-idea files
    for idea_file in output_dir.glob("raw-idea-*.json"):
        with open(idea_file, 'r') as f:
            idea = json.load(f)
            # Only process APPROVED ideas
            if idea.get("status") == "APPROVED":
                ideas.append(idea)

    # Sort by timestamp (most recent first) if ideas have timestamps
    if ideas and 'timestamp' in ideas[0]:
        ideas.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # In demo mode, only process the most recent approved idea
    if limit_one and ideas:
        ideas = [ideas[0]]
        print(f"   ✅ Loaded latest approved idea: {ideas[0].get('title')}")
    else:
        print(f"   ✅ Loaded {len(ideas)} approved idea{'s' if len(ideas) != 1 else ''}")

    return ideas


def analyze_scope(idea):
    """
    Use Claude to analyze scope and complexity of a data product idea.

    Args:
        idea: Approved idea dictionary

    Returns:
        Scope challenge dictionary
    """
    system_prompt = """You are the Scope Agent - think of yourself as a tough Shark Tank investor focused on COMPLEXITY and EXECUTION RISK.

Your job is to be SKEPTICAL and challenge assumptions. You've seen too many projects fail due to scope creep and hidden complexity.

Be TOUGH:
- Don't sugarcoat complexity - if it's complex, say it
- Call out unrealistic scope assumptions
- Question whether the team can actually execute this
- Identify every integration point that could fail
- Be skeptical of "simple" estimates

But also be CONSTRUCTIVE:
- Offer real ways to reduce scope
- Suggest phased approaches
- Identify quick wins vs. multi-year initiatives

Remember: You're protecting the organization from overpromising and underdelivering.
If this idea is going to fail, better to know now than after 6 months of wasted effort."""

    prompt = f"""Analyze the scope and complexity of this data product idea:

IDEA: {idea.get('title')}
DESCRIPTION: {idea.get('description')}
DOMAIN: {idea.get('domain')}
RELATED TOPICS: {json.dumps(idea.get('related_topics', []))}
INITIAL COMPLEXITY: {idea.get('estimated_complexity')}
REASONING: {idea.get('reasoning')}

Provide a detailed scope analysis covering:

1. **Complexity Rating**: Assess true complexity (TRIVIAL, SIMPLE, MODERATE, COMPLEX, VERY_COMPLEX)

2. **Scope Creep Risk**: How likely is this to expand beyond estimates? (MINIMAL, LOW, MODERATE, HIGH, CRITICAL)

3. **Technical Challenges**: List 3-5 specific technical challenges (e.g., "Schema evolution for high-traffic topics", "Real-time aggregation at scale")

4. **Integration Points**: What systems/services need integration? (e.g., "Kafka Streams app", "REST API", "Schema Registry")

5. **Dependencies**: What's needed before starting? (e.g., "Consumer group quota increase", "ksqlDB cluster provisioning")

6. **Scope Adjustments**: Suggest 2-3 ways to reduce scope or manage complexity (e.g., "Start with read-only API, add write later", "Implement for single domain first")

7. **Reasoning**: Detailed explanation of your assessment

Respond in JSON format:
{{
  "complexity_rating": "MODERATE",
  "scope_creep_risk": "MODERATE",
  "technical_challenges": ["challenge1", "challenge2", "challenge3"],
  "integration_points": ["integration1", "integration2"],
  "dependencies": ["dependency1", "dependency2"],
  "recommended_scope_adjustments": ["adjustment1", "adjustment2"],
  "confidence_score": 0.8,
  "reasoning": "Detailed explanation..."
}}"""

    response = call_claude(system_prompt, prompt)

    try:
        # Parse JSON from Claude's response
        # Handle cases where Claude wraps JSON in markdown code blocks
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```
        response_text = response_text.strip()

        analysis = json.loads(response_text)

        # Build scope challenge
        challenge = {
            "timestamp": datetime.now(UTC).isoformat(),
            "challenge_id": str(uuid.uuid4()),
            "idea_id": idea.get("idea_id"),
            "idea_title": idea.get("title"),
            "complexity_rating": analysis.get("complexity_rating", "MODERATE"),
            "scope_creep_risk": analysis.get("scope_creep_risk", "MODERATE"),
            "technical_challenges": analysis.get("technical_challenges", []),
            "integration_points": analysis.get("integration_points", []),
            "dependencies": analysis.get("dependencies", []),
            "recommended_scope_adjustments": analysis.get("recommended_scope_adjustments", []),
            "confidence_score": analysis.get("confidence_score", 0.7),
            "reasoning": analysis.get("reasoning", "")
        }

        return challenge

    except json.JSONDecodeError as e:
        print(f"   ⚠️  Failed to parse Claude response as JSON: {e}")
        print(f"   Response: {response[:200]}...")
        # Return a fallback challenge
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "challenge_id": str(uuid.uuid4()),
            "idea_id": idea.get("idea_id"),
            "idea_title": idea.get("title"),
            "complexity_rating": "MODERATE",
            "scope_creep_risk": "MODERATE",
            "technical_challenges": ["Unable to parse detailed analysis"],
            "integration_points": [],
            "dependencies": [],
            "recommended_scope_adjustments": [],
            "confidence_score": 0.5,
            "reasoning": "Scope analysis failed to parse. Manual review recommended."
        }


def save_challenge_to_file(challenge):
    """Save scope challenge to dry-run output file."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"
    output_dir.mkdir(exist_ok=True)

    filename = f"scope-challenge-{challenge['challenge_id']}.json"
    output_file = output_dir / filename

    with open(output_file, 'w') as f:
        json.dump(challenge, f, indent=2)

    print(f"   💾 Saved to {filename}")


def publish_scope_challenge(challenge, dry_run=False):
    """Publish scope challenge to Kafka topic or file."""
    if dry_run:
        save_challenge_to_file(challenge)
        return True

    # Kafka publishing logic (for future full mode)
    schema_str = get_schema_string("scope-challenge")
    producer, serializer = create_avro_producer(schema_str)

    success = produce_message(
        producer,
        serializer,
        "agent-state-scope-challenges",
        challenge["idea_id"],
        challenge
    )

    if success:
        print("   ✅ Scope challenge published successfully!")
    else:
        print("   ❌ Failed to publish scope challenge")

    return success


def run_scope_agent(dry_run=False, limit_one=False):
    """Main scope agent execution."""
    print("\n" + "=" * 60)
    print("SCOPE AGENT - Complexity & Integration Analysis")
    print("=" * 60)

    # Load approved ideas
    if dry_run:
        ideas = load_approved_ideas_from_files(limit_one=limit_one)
    else:
        ideas = load_approved_ideas_from_kafka(limit_one=limit_one)

    if not ideas:
        print("\n⚠️  No approved ideas found to evaluate")
        return []

    print(f"\n2. Analyzing scope for {len(ideas)} approved ideas...")

    challenges = []
    for i, idea in enumerate(ideas, 1):
        print(f"\n   [{i}/{len(ideas)}] Analyzing: {idea.get('title')}")
        challenge = analyze_scope(idea)
        challenges.append(challenge)

        print(f"      Complexity: {challenge['complexity_rating']}")
        print(f"      Scope Risk: {challenge['scope_creep_risk']}")
        print(f"      Challenges: {len(challenge['technical_challenges'])}")

        # Publish the challenge
        publish_scope_challenge(challenge, dry_run=dry_run)

    print("\n" + "=" * 60)
    print(f"SCOPE AGENT COMPLETE - Generated {len(challenges)} challenges")
    print("=" * 60 + "\n")

    return challenges


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scope Agent - Analyzes complexity and scope of data product ideas"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (read/write files instead of Kafka)"
    )
    parser.add_argument(
        "--limit-one",
        action="store_true",
        help="Only process the most recent approved idea (demo mode)"
    )
    args = parser.parse_args()

    run_scope_agent(dry_run=args.dry_run, limit_one=args.limit_one)
