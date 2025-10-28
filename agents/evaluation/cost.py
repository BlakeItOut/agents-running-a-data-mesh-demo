#!/usr/bin/env python3
"""
Cost Agent - Evaluation Layer

Analyzes approved data product ideas for:
- Development and operational costs
- Resource requirements (people, infrastructure)
- Cost risks and ROI potential
- Cost optimization opportunities

Consumes refined/approved ideas and publishes cost challenges.
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
        group_id=f"cost-agent-{datetime.now().timestamp()}"  # Unique group to read all messages
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


def analyze_costs(idea):
    """
    Use Claude to estimate costs and resource requirements.

    Args:
        idea: Approved idea dictionary

    Returns:
        Cost challenge dictionary
    """
    system_prompt = """You are the Cost Agent - think of yourself as Kevin O'Leary from Shark Tank. You care about MONEY and ROI, period.

Every dollar spent on this needs to generate value. You're RUTHLESS about costs and skeptical of "it'll pay for itself" claims.

Be TOUGH on costs:
- Don't lowball estimates - projects ALWAYS cost more than expected
- Hidden costs are everywhere: testing envs, monitoring, oncall, maintenance, technical debt
- Developer time is EXPENSIVE ($200/hr fully loaded)
- Infrastructure costs add up FAST (Confluent Cloud ain't cheap)
- Question the ROI - "How exactly does this make us money?"

Be SKEPTICAL of value:
- "Nice to have" is code for "waste of money"
- If they can't quantify the value, it's probably not worth it
- Operational costs last FOREVER - that $500/month becomes $6K/year, $30K over 5 years
- What's the REAL cost if this project fails halfway through?

But be STRATEGIC:
- Identify cost optimization opportunities (do it cheaper)
- Suggest MVP approaches (prove value before big investment)
- Compare to buying vs. building

Remember: "I'm out" if the numbers don't make sense. This is business, not a charity."""

    prompt = f"""Estimate the costs for implementing this data product idea:

IDEA: {idea.get('title')}
DESCRIPTION: {idea.get('description')}
DOMAIN: {idea.get('domain')}
RELATED TOPICS: {json.dumps(idea.get('related_topics', []))}
COMPLEXITY: {idea.get('estimated_complexity')}
REASONING: {idea.get('reasoning')}

Provide a detailed cost analysis covering:

1. **Development Cost Estimate** (in USD):
   - Low: Optimistic estimate
   - Medium: Realistic estimate
   - High: Conservative estimate

2. **Monthly Operational Cost**: Ongoing infrastructure and maintenance costs (USD/month)

3. **Resource Requirements**: List needed resources with:
   - Type (e.g., "Data Engineer", "Backend Developer", "DevOps Engineer")
   - Count (FTE or fraction, e.g., 1.5 for full-time + part-time)
   - Duration (weeks)

4. **Infrastructure Costs**: Break down Kafka/streaming infrastructure:
   - Component (e.g., "Kafka topics storage", "ksqlDB application", "Connectors")
   - Monthly cost (USD)
   - Notes

5. **Cost Risk**: Likelihood of exceeding estimates (MINIMAL, LOW, MODERATE, HIGH, CRITICAL)

6. **ROI Potential**: Expected return on investment (MINIMAL, LOW, MODERATE, HIGH, VERY_HIGH)

7. **Cost Optimization Opportunities**: Ways to reduce costs

8. **Reasoning**: Detailed explanation of your cost assessment

Consider:
- Confluent Cloud pricing (topics, partitions, connectors, throughput)
- Developer time at $150-200/hour
- Kafka Streams/ksqlDB application hosting
- Schema Registry usage
- Testing environments
- Monitoring and observability

Respond in JSON format:
{{
  "development_cost_estimate": {{
    "low": 25000.0,
    "medium": 40000.0,
    "high": 60000.0
  }},
  "monthly_operational_cost": 500.0,
  "resource_requirements": [
    {{"type": "Data Engineer", "count": 1.0, "duration_weeks": 6.0}},
    {{"type": "Backend Developer", "count": 0.5, "duration_weeks": 4.0}}
  ],
  "infrastructure_costs": [
    {{"component": "Kafka topics", "monthly_cost": 200.0, "notes": "3 topics, moderate throughput"}},
    {{"component": "ksqlDB app", "monthly_cost": 300.0, "notes": "Processing and aggregation"}}
  ],
  "cost_risk": "MODERATE",
  "roi_potential": "HIGH",
  "cost_optimization_opportunities": ["opportunity1", "opportunity2"],
  "confidence_score": 0.7,
  "reasoning": "Detailed explanation..."
}}"""

    response = call_claude(system_prompt, prompt)

    try:
        # Parse JSON from Claude's response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        analysis = json.loads(response_text)

        # Build cost challenge
        challenge = {
            "timestamp": datetime.now(UTC).isoformat(),
            "challenge_id": str(uuid.uuid4()),
            "idea_id": idea.get("idea_id"),
            "idea_title": idea.get("title"),
            "development_cost_estimate": analysis.get("development_cost_estimate", {
                "low": 20000.0,
                "medium": 35000.0,
                "high": 50000.0
            }),
            "monthly_operational_cost": analysis.get("monthly_operational_cost", 400.0),
            "resource_requirements": analysis.get("resource_requirements", []),
            "infrastructure_costs": analysis.get("infrastructure_costs", []),
            "cost_risk": analysis.get("cost_risk", "MODERATE"),
            "roi_potential": analysis.get("roi_potential", "MODERATE"),
            "cost_optimization_opportunities": analysis.get("cost_optimization_opportunities", []),
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
            "development_cost_estimate": {
                "low": 20000.0,
                "medium": 35000.0,
                "high": 50000.0
            },
            "monthly_operational_cost": 400.0,
            "resource_requirements": [],
            "infrastructure_costs": [],
            "cost_risk": "MODERATE",
            "roi_potential": "MODERATE",
            "cost_optimization_opportunities": ["Unable to parse detailed analysis"],
            "confidence_score": 0.5,
            "reasoning": "Cost analysis failed to parse. Manual review recommended."
        }


def save_challenge_to_file(challenge):
    """Save cost challenge to dry-run output file."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"
    output_dir.mkdir(exist_ok=True)

    filename = f"cost-challenge-{challenge['challenge_id']}.json"
    output_file = output_dir / filename

    with open(output_file, 'w') as f:
        json.dump(challenge, f, indent=2)

    print(f"   💾 Saved to {filename}")


def publish_cost_challenge(challenge, dry_run=False):
    """Publish cost challenge to Kafka topic or file."""
    if dry_run:
        save_challenge_to_file(challenge)
        return True

    # Kafka publishing logic (for future full mode)
    schema_str = get_schema_string("cost-challenge")
    producer, serializer = create_avro_producer(schema_str)

    success = produce_message(
        producer,
        serializer,
        "agent-state-cost-challenges",
        challenge["idea_id"],
        challenge
    )

    if success:
        print("   ✅ Cost challenge published successfully!")
    else:
        print("   ❌ Failed to publish cost challenge")

    return success


def run_cost_agent(dry_run=False, limit_one=False):
    """Main cost agent execution."""
    print("\n" + "=" * 60)
    print("COST AGENT - Resource & Budget Analysis")
    print("=" * 60)

    # Load approved ideas
    if dry_run:
        ideas = load_approved_ideas_from_files(limit_one=limit_one)
    else:
        ideas = load_approved_ideas_from_kafka(limit_one=limit_one)

    if not ideas:
        print("\n⚠️  No approved ideas found to evaluate")
        return []

    print(f"\n2. Analyzing costs for {len(ideas)} approved ideas...")

    challenges = []
    for i, idea in enumerate(ideas, 1):
        print(f"\n   [{i}/{len(ideas)}] Analyzing: {idea.get('title')}")
        challenge = analyze_costs(idea)
        challenges.append(challenge)

        dev_cost = challenge['development_cost_estimate']
        print(f"      Dev Cost: ${dev_cost['low']:,.0f} - ${dev_cost['high']:,.0f}")
        print(f"      Monthly Op: ${challenge['monthly_operational_cost']:,.0f}")
        print(f"      ROI: {challenge['roi_potential']}")

        # Publish the challenge
        publish_cost_challenge(challenge, dry_run=dry_run)

    print("\n" + "=" * 60)
    print(f"COST AGENT COMPLETE - Generated {len(challenges)} challenges")
    print("=" * 60 + "\n")

    return challenges


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cost Agent - Estimates costs and resource requirements"
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

    run_cost_agent(dry_run=args.dry_run, limit_one=args.limit_one)
