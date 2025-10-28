#!/usr/bin/env python3
"""
Time Agent - Evaluation Layer

Analyzes approved data product ideas for:
- Implementation timeline estimates
- Schedule risks
- Implementation phases
- Parallel work opportunities

Consumes refined/approved ideas and publishes time challenges.
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


def analyze_timeline(idea):
    """
    Use Claude to estimate timeline and assess schedule risks.

    Args:
        idea: Approved idea dictionary

    Returns:
        Time challenge dictionary
    """
    system_prompt = """You are the Time Agent - think of yourself as a tough Shark Tank investor focused on TIME and SCHEDULE RISK.

You've seen EVERY timeline estimate turn out to be 2-3x too optimistic. Your job is to inject REALITY.

Be SKEPTICAL:
- Multiply initial estimates by 2-3x (real-world tax)
- Call out hidden time sinks: testing, reviews, rework, integration debugging
- Question "it should only take a week" assumptions
- Remember: things ALWAYS take longer than expected
- Consider real-world interruptions, context switching, dependencies on other teams

Be TOUGH but FAIR:
- Provide realistic best/expected/worst case scenarios
- Your "best case" should be someone else's "expected case"
- Identify what will cause delays (because something always does)
- Suggest ways to de-risk the timeline

Remember: "You're dead to me if you miss this deadline" - better to set realistic expectations upfront than fail to deliver on time."""

    prompt = f"""Estimate the timeline for implementing this data product idea:

IDEA: {idea.get('title')}
DESCRIPTION: {idea.get('description')}
DOMAIN: {idea.get('domain')}
RELATED TOPICS: {json.dumps(idea.get('related_topics', []))}
COMPLEXITY: {idea.get('estimated_complexity')}
REASONING: {idea.get('reasoning')}

Provide a detailed timeline analysis covering:

1. **Duration Estimates** (in weeks):
   - Best case: Optimistic scenario
   - Expected: Realistic estimate
   - Worst case: If things go wrong

2. **Schedule Risk**: Overall timeline risk (MINIMAL, LOW, MODERATE, HIGH, CRITICAL)

3. **Implementation Phases**: Break down into 3-5 phases with:
   - Phase name
   - Duration (weeks)
   - Description of work

4. **Time Risk Factors**: List 3-5 things that could delay the timeline

5. **Parallel Work Opportunities**: What can be done simultaneously to save time?

6. **Reasoning**: Detailed explanation of your timeline assessment

Consider factors like:
- Kafka Streams app development and testing
- Schema design and evolution
- Consumer integration
- Testing and QA
- Documentation
- Code review and approval cycles

Respond in JSON format:
{{
  "estimated_duration_weeks": 6.0,
  "best_case_weeks": 4.0,
  "worst_case_weeks": 10.0,
  "schedule_risk": "MODERATE",
  "implementation_phases": [
    {{"name": "Phase 1", "duration_weeks": 2.0, "description": "Initial setup"}},
    {{"name": "Phase 2", "duration_weeks": 3.0, "description": "Core development"}},
    {{"name": "Phase 3", "duration_weeks": 1.0, "description": "Testing and deployment"}}
  ],
  "time_risk_factors": ["risk1", "risk2", "risk3"],
  "parallel_work_opportunities": ["opportunity1", "opportunity2"],
  "confidence_score": 0.75,
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

        # Build time challenge
        challenge = {
            "timestamp": datetime.now(UTC).isoformat(),
            "challenge_id": str(uuid.uuid4()),
            "idea_id": idea.get("idea_id"),
            "idea_title": idea.get("title"),
            "estimated_duration_weeks": analysis.get("estimated_duration_weeks", 6.0),
            "best_case_weeks": analysis.get("best_case_weeks", 4.0),
            "worst_case_weeks": analysis.get("worst_case_weeks", 10.0),
            "schedule_risk": analysis.get("schedule_risk", "MODERATE"),
            "implementation_phases": analysis.get("implementation_phases", []),
            "time_risk_factors": analysis.get("time_risk_factors", []),
            "parallel_work_opportunities": analysis.get("parallel_work_opportunities", []),
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
            "estimated_duration_weeks": 6.0,
            "best_case_weeks": 4.0,
            "worst_case_weeks": 10.0,
            "schedule_risk": "MODERATE",
            "implementation_phases": [],
            "time_risk_factors": ["Unable to parse detailed analysis"],
            "parallel_work_opportunities": [],
            "confidence_score": 0.5,
            "reasoning": "Timeline analysis failed to parse. Manual review recommended."
        }


def save_challenge_to_file(challenge):
    """Save time challenge to dry-run output file."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"
    output_dir.mkdir(exist_ok=True)

    filename = f"time-challenge-{challenge['challenge_id']}.json"
    output_file = output_dir / filename

    with open(output_file, 'w') as f:
        json.dump(challenge, f, indent=2)

    print(f"   💾 Saved to {filename}")


def publish_time_challenge(challenge, dry_run=False):
    """Publish time challenge to Kafka topic or file."""
    if dry_run:
        save_challenge_to_file(challenge)
        return True

    # Kafka publishing logic (for future full mode)
    schema_str = get_schema_string("time-challenge")
    producer, serializer = create_avro_producer(schema_str)

    success = produce_message(
        producer,
        serializer,
        "agent-state-time-challenges",
        challenge,
        key=challenge["idea_id"]
    )

    if success:
        print("   ✅ Time challenge published successfully!")
    else:
        print("   ❌ Failed to publish time challenge")

    return success


def run_time_agent(dry_run=False, limit_one=False):
    """Main time agent execution."""
    print("\n" + "=" * 60)
    print("TIME AGENT - Timeline & Schedule Risk Analysis")
    print("=" * 60)

    # Load approved ideas
    ideas = load_approved_ideas_from_files(limit_one=limit_one) if dry_run else []

    if not ideas:
        print("\n⚠️  No approved ideas found to evaluate")
        return []

    print(f"\n2. Estimating timelines for {len(ideas)} approved ideas...")

    challenges = []
    for i, idea in enumerate(ideas, 1):
        print(f"\n   [{i}/{len(ideas)}] Analyzing: {idea.get('title')}")
        challenge = analyze_timeline(idea)
        challenges.append(challenge)

        print(f"      Estimate: {challenge['estimated_duration_weeks']} weeks")
        print(f"      Range: {challenge['best_case_weeks']}-{challenge['worst_case_weeks']} weeks")
        print(f"      Risk: {challenge['schedule_risk']}")

        # Publish the challenge
        publish_time_challenge(challenge, dry_run=dry_run)

    print("\n" + "=" * 60)
    print(f"TIME AGENT COMPLETE - Generated {len(challenges)} challenges")
    print("=" * 60 + "\n")

    return challenges


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Time Agent - Estimates timeline and schedule risks"
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

    run_time_agent(dry_run=args.dry_run, limit_one=args.limit_one)
