#!/usr/bin/env python3
"""
Learning Agent

Consumes from agent-state-current topic and generates data product ideas.
Uses Claude to analyze current state and propose data products based on:
- Domain groupings
- Usage patterns
- Infrastructure opportunities

Publishes raw ideas to agent-state-raw-ideas topic for human refinement.
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


def load_current_state_from_file():
    """Load current state from dry-run output file."""
    print("\n1. Loading current state from dry-run output...")

    output_dir = Path(__file__).parent.parent / "dry-run-output"
    current_state_file = output_dir / "current-state.json"

    if current_state_file.exists():
        with open(current_state_file, 'r') as f:
            current_state = json.load(f)
        print("   ✅ Loaded current-state.json")
        return current_state
    else:
        print("   ⚠️  File not found!")
        return {}


def consume_current_state(dry_run=False):
    """
    Consume latest message from agent-state-current topic.
    In dry-run mode, reads from file instead of Kafka.
    """
    if dry_run:
        return load_current_state_from_file()

    print("\n1. Consuming from agent-state-current topic...")

    schema_str = get_schema_string("current-state")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id="learning-agent"
    )

    current_state = consume_latest_message(
        consumer,
        deserializer,
        "agent-state-current",
        timeout=5.0
    )

    if not current_state:
        print("   ⚠️  No current state found!")
        return {}

    print("   ✅ Consumed current state")
    return current_state


def generate_data_product_ideas(current_state):
    """
    Use Claude to generate data product ideas based on current state.

    Args:
        current_state: Current platform state with deployment, usage, metrics

    Returns:
        List of raw idea dictionaries
    """
    system_prompt = """You are the Learning Agent for a data mesh platform.

Your mission: Analyze the current state of data infrastructure and propose valuable data products.

A data product is a well-defined, discoverable, and governed collection of related data streams
that serves a specific business purpose.

Key principles:
1. Group related topics by domain (e.g., gaming, e-commerce, fleet management)
2. Consider usage patterns - prioritize high-traffic or underutilized topics
3. Look for natural business boundaries
4. Think about potential consumers and use cases
5. Be practical - data products should be implementable and maintainable

Your proposals should be specific, actionable, and value-driven."""

    # Extract summary info for Claude
    deployment = current_state.get("deployment", {})
    usage = current_state.get("usage", {})
    metrics = current_state.get("metrics", {})
    summary = current_state.get("summary", "")
    observations = current_state.get("notable_observations", [])

    prompt = f"""Analyze this data platform state and propose 3-5 data product ideas:

PLATFORM SUMMARY:
{summary}

NOTABLE OBSERVATIONS:
{json.dumps(observations, indent=2)}

DEPLOYMENT INFO:
- Total Topics: {deployment.get('total_topics', 0)}
- Domains: {deployment.get('domain_count', 0)}
- Schemas: {deployment.get('total_schemas', 0)}

USAGE INFO:
- Consumer Groups: {usage.get('consumer_groups', 0)}
- Active Consumers: {usage.get('active_consumers', 0)}
- Idle Topics: {usage.get('idle_topic_count', 0)}

METRICS INFO:
- Throughput: {metrics.get('total_throughput_mbps', 0)} MB/s
- Avg Latency: {metrics.get('avg_latency_ms', 0)} ms
- Topics with Lag: {metrics.get('topics_with_lag_count', 0)}

Based on this state, propose 3-5 data product ideas. Think about:
- Gaming domain (gaming_games, gaming_players, gaming_player_activity)
- E-commerce domain (orders, inventory, product, ratings, shoes, stores, etc.)
- Fleet Management (location, sensors, description)
- Financial (transactions, credit_cards, stock_trades, campaign_finance)
- Pizza delivery (orders, cancellations, completions)
- Insurance (customers, offers, activity)
- Web analytics (clickstream, pageviews, users)
- HR/Payroll (employee, location, bonus)

For each idea, provide:
1. A compelling title
2. Detailed description of the data product
3. Which specific topics would be included (use actual topic names from the domains above)
4. The primary domain
5. Reasoning based on the current state
6. Potential users/consumers
7. Estimated complexity (LOW/MEDIUM/HIGH/VERY_HIGH)
8. Your confidence score (0.0-1.0)

Respond in this JSON format:
{{
  "ideas": [
    {{
      "title": "Gaming Analytics Hub",
      "description": "Comprehensive gaming data product combining player activity, game metadata, and engagement metrics for analytics and ML",
      "related_topics": ["gaming_games", "gaming_players", "gaming_player_activity"],
      "domain": "gaming",
      "reasoning": "These three topics are tightly coupled and represent a complete gaming domain. High value for analytics teams.",
      "potential_users": ["Data Scientists", "Game Analysts", "Product Managers"],
      "estimated_complexity": "MEDIUM",
      "confidence_score": 0.85
    }}
  ]
}}
"""

    print("   🤖 Calling Claude to generate ideas...")
    response = call_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.7,  # Higher temperature for creativity
        max_tokens=4096
    )

    # Parse response
    try:
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        parsed = json.loads(json_str)
        ideas = parsed.get("ideas", [])

        print(f"   ✅ Generated {len(ideas)} ideas")
        return ideas

    except (json.JSONDecodeError, IndexError) as e:
        print(f"   ⚠️  Failed to parse Claude response: {e}")
        print(f"   Response preview: {response[:200]}...")
        return []


def create_raw_idea_message(idea_data):
    """
    Convert idea data from Claude into RawIdea message format.

    Args:
        idea_data: Dictionary with idea fields from Claude

    Returns:
        RawIdea message matching Avro schema
    """
    timestamp = datetime.now(UTC).isoformat()
    idea_id = str(uuid.uuid4())

    return {
        "timestamp": timestamp,
        "idea_id": idea_id,
        "title": idea_data.get("title", "Untitled Idea"),
        "description": idea_data.get("description", "No description provided"),
        "domain": idea_data.get("domain", "unknown"),
        "related_topics": idea_data.get("related_topics", []),
        "reasoning": idea_data.get("reasoning", "No reasoning provided"),
        "potential_users": idea_data.get("potential_users", []),
        "estimated_complexity": idea_data.get("estimated_complexity", "MEDIUM"),
        "confidence_score": float(idea_data.get("confidence_score", 0.5)),
        "status": "RAW"
    }


def run_learning_agent(dry_run=False):
    """Main learning agent logic"""
    print("=" * 60)
    print("LEARNING AGENT" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    # Step 1: Consume current state
    current_state = consume_current_state(dry_run=dry_run)

    if not current_state:
        print("\n❌ No current state available. Run bootstrap.py first!")
        return []

    # Step 2: Generate data product ideas with Claude
    print("\n2. Generating data product ideas with Claude...")
    ideas = generate_data_product_ideas(current_state)

    if not ideas:
        print("\n⚠️  No ideas generated!")
        return []

    # Step 3: Convert to RawIdea messages and publish
    print(f"\n3. Publishing {len(ideas)} ideas...")

    raw_ideas = []
    for i, idea_data in enumerate(ideas, 1):
        raw_idea = create_raw_idea_message(idea_data)
        raw_ideas.append(raw_idea)

        print(f"\n   Idea {i}: {raw_idea['title']}")
        print(f"   Domain: {raw_idea['domain']}")
        print(f"   Topics: {len(raw_idea['related_topics'])}")
        print(f"   Complexity: {raw_idea['estimated_complexity']}")
        print(f"   Confidence: {raw_idea['confidence_score']:.2f}")

        if dry_run:
            # Save to file
            output_dir = Path(__file__).parent.parent / "dry-run-output"
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"raw-idea-{raw_idea['idea_id']}.json"

            with open(output_file, 'w') as f:
                json.dump(raw_idea, f, indent=2)

            print(f"   💾 Saved to {output_file.name}")
        else:
            # Publish to Kafka
            try:
                schema_str = get_schema_string("raw-ideas")
                producer, serializer = create_avro_producer(schema_str)

                produce_message(
                    producer=producer,
                    serializer=serializer,
                    topic="agent-state-raw-ideas",
                    key=raw_idea['idea_id'],
                    value=raw_idea
                )

                print(f"   ✅ Published to Kafka")

            except Exception as e:
                print(f"   ❌ Failed to publish: {e}")
                raise

    print("\n" + "=" * 60)
    print("LEARNING AGENT COMPLETE")
    print("=" * 60)
    print(f"\n✨ Generated {len(raw_ideas)} data product ideas!")
    print("\n💡 Next step: Human review and refinement of ideas")

    return raw_ideas


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Learning Agent - Generates data product ideas from current state"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: read from files and save output to file instead of using Kafka"
    )
    args = parser.parse_args()

    ideas = run_learning_agent(dry_run=args.dry_run)

    # Print summary
    if ideas:
        print("\nGenerated Ideas:")
        for i, idea in enumerate(ideas, 1):
            print(f"\n{i}. {idea['title']}")
            print(f"   {idea['description']}")
            print(f"   Topics: {', '.join(idea['related_topics'][:3])}{'...' if len(idea['related_topics']) > 3 else ''}")
