#!/usr/bin/env python3
"""
Decision Agent - Evaluation Layer

Synthesizes scope, time, and cost challenges into a final recommendation.
Acts like the Shark Tank panel reaching a consensus after all sharks have weighed in.

Consumes the three challenges and produces a decision with overall recommendation.
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


def load_challenges_from_files(idea_id):
    """Load scope, time, and cost challenges for a specific idea from dry-run output files."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"

    challenges = {
        "scope": None,
        "time": None,
        "cost": None
    }

    # Find challenge files for this idea
    for scope_file in output_dir.glob("scope-challenge-*.json"):
        with open(scope_file, 'r') as f:
            challenge = json.load(f)
            if challenge.get("idea_id") == idea_id:
                challenges["scope"] = challenge
                break

    for time_file in output_dir.glob("time-challenge-*.json"):
        with open(time_file, 'r') as f:
            challenge = json.load(f)
            if challenge.get("idea_id") == idea_id:
                challenges["time"] = challenge
                break

    for cost_file in output_dir.glob("cost-challenge-*.json"):
        with open(cost_file, 'r') as f:
            challenge = json.load(f)
            if challenge.get("idea_id") == idea_id:
                challenges["cost"] = challenge
                break

    return challenges


def load_challenges_from_kafka():
    """Load all challenges from Kafka topics and group by idea_id."""
    print("   Loading challenges from Kafka...")

    challenges_by_idea = {}

    # Load scope challenges
    print("      - Loading scope challenges...")
    schema_str = get_schema_string("scope-challenge")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"decision-agent-scope-{datetime.now().timestamp()}"
    )
    consumer.subscribe(["agent-state-scope-challenges"])

    try:
        timeout_ms = 5000
        while True:
            msg = consumer.poll(timeout=timeout_ms / 1000.0)
            if msg is None:
                break
            if msg.error():
                continue

            value = deserializer(msg.value(), None)
            if value:
                idea_id = value.get("idea_id")
                if idea_id not in challenges_by_idea:
                    challenges_by_idea[idea_id] = {}
                challenges_by_idea[idea_id]["scope"] = value
    finally:
        consumer.close()

    # Load time challenges
    print("      - Loading time challenges...")
    schema_str = get_schema_string("time-challenge")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"decision-agent-time-{datetime.now().timestamp()}"
    )
    consumer.subscribe(["agent-state-time-challenges"])

    try:
        timeout_ms = 5000
        while True:
            msg = consumer.poll(timeout=timeout_ms / 1000.0)
            if msg is None:
                break
            if msg.error():
                continue

            value = deserializer(msg.value(), None)
            if value:
                idea_id = value.get("idea_id")
                if idea_id not in challenges_by_idea:
                    challenges_by_idea[idea_id] = {}
                challenges_by_idea[idea_id]["time"] = value
    finally:
        consumer.close()

    # Load cost challenges
    print("      - Loading cost challenges...")
    schema_str = get_schema_string("cost-challenge")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"decision-agent-cost-{datetime.now().timestamp()}"
    )
    consumer.subscribe(["agent-state-cost-challenges"])

    try:
        timeout_ms = 5000
        while True:
            msg = consumer.poll(timeout=timeout_ms / 1000.0)
            if msg is None:
                break
            if msg.error():
                continue

            value = deserializer(msg.value(), None)
            if value:
                idea_id = value.get("idea_id")
                if idea_id not in challenges_by_idea:
                    challenges_by_idea[idea_id] = {}
                challenges_by_idea[idea_id]["cost"] = value
    finally:
        consumer.close()

    # Filter to only ideas with all three challenges
    complete_ideas = {
        idea_id: challenges
        for idea_id, challenges in challenges_by_idea.items()
        if "scope" in challenges and "time" in challenges and "cost" in challenges
    }

    print(f"      ✅ Found {len(complete_ideas)} ideas with complete challenges")
    return complete_ideas


def load_all_idea_ids():
    """Get list of idea IDs that have all three challenges."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"

    # Get all scope challenge idea IDs
    idea_ids = set()
    for scope_file in output_dir.glob("scope-challenge-*.json"):
        with open(scope_file, 'r') as f:
            challenge = json.load(f)
            idea_ids.add(challenge.get("idea_id"))

    return list(idea_ids)


def synthesize_decision(idea_title, scope_challenge, time_challenge, cost_challenge):
    """
    Use Claude to synthesize all three challenges into a final decision.

    Args:
        idea_title: Title of the idea
        scope_challenge: Scope challenge dict
        time_challenge: Time challenge dict
        cost_challenge: Cost challenge dict

    Returns:
        Decision dictionary
    """
    system_prompt = """You are the Decision Agent - you're the panel of Shark Tank investors after hearing pitches from three skeptical sharks.

You've heard from:
- The SCOPE shark (complexity and execution risk)
- The TIME shark (timeline and schedule risk)
- The COST shark (money and ROI)

Your job: Synthesize their concerns into a FINAL DECISION.

Be DECISIVE:
- STRONGLY_APPROVE: All sharks see green lights, low risk, high value
- APPROVE: Good idea with manageable risks
- APPROVE_WITH_CONDITIONS: "I'm in, BUT..." - needs changes/de-risking
- RECONSIDER: Red flags everywhere - needs major rethinking
- REJECT: "I'm out" - not worth the investment

Consider:
- Do the risks outweigh the benefits?
- Can conditions make a risky idea acceptable?
- Is the ROI worth the time and complexity?
- What would make this a slam dunk?

Be honest and direct. Organizations need clear decisions, not wishy-washy maybes."""

    prompt = f"""Here's what each shark said about "{idea_title}":

━━━ SCOPE SHARK ━━━
Complexity: {scope_challenge.get('complexity_rating')}
Scope Creep Risk: {scope_challenge.get('scope_creep_risk')}
Technical Challenges ({len(scope_challenge.get('technical_challenges', []))}):
{json.dumps(scope_challenge.get('technical_challenges', []), indent=2)}
Integration Points: {json.dumps(scope_challenge.get('integration_points', []), indent=2)}
Dependencies: {json.dumps(scope_challenge.get('dependencies', []), indent=2)}
Recommended Adjustments: {json.dumps(scope_challenge.get('recommended_scope_adjustments', []), indent=2)}

Reasoning: {scope_challenge.get('reasoning')}

━━━ TIME SHARK ━━━
Timeline: {time_challenge.get('best_case_weeks')}-{time_challenge.get('worst_case_weeks')} weeks (expected: {time_challenge.get('estimated_duration_weeks')})
Schedule Risk: {time_challenge.get('schedule_risk')}
Phases: {len(time_challenge.get('implementation_phases', []))}
Time Risks: {json.dumps(time_challenge.get('time_risk_factors', []), indent=2)}
Parallel Opportunities: {json.dumps(time_challenge.get('parallel_work_opportunities', []), indent=2)}

Reasoning: {time_challenge.get('reasoning')}

━━━ COST SHARK ━━━
Development Cost: ${cost_challenge.get('development_cost_estimate', {}).get('low', 0):,.0f} - ${cost_challenge.get('development_cost_estimate', {}).get('high', 0):,.0f}
Monthly Operations: ${cost_challenge.get('monthly_operational_cost', 0):,.0f}/month
Cost Risk: {cost_challenge.get('cost_risk')}
ROI Potential: {cost_challenge.get('roi_potential')}
Resources: {len(cost_challenge.get('resource_requirements', []))} roles needed
Infrastructure: {len(cost_challenge.get('infrastructure_costs', []))} components
Cost Optimizations: {json.dumps(cost_challenge.get('cost_optimization_opportunities', []), indent=2)}

Reasoning: {cost_challenge.get('reasoning')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on these three perspectives, make your FINAL DECISION.

Provide:
1. **Recommendation**: STRONGLY_APPROVE, APPROVE, APPROVE_WITH_CONDITIONS, RECONSIDER, or REJECT
2. **Overall Risk**: MINIMAL, LOW, MODERATE, HIGH, or CRITICAL
3. **Key Findings**: 3-5 most important insights (combine all three sharks' input)
4. **Conditions** (if APPROVE_WITH_CONDITIONS): What must change/happen for approval
5. **Alternative Approaches**: Other ways to achieve the goal with less risk/cost
6. **Summary**: 2-3 sentence executive summary
7. **Detailed Reasoning**: Synthesis of scope + time + cost analysis

Respond in JSON format:
{{
  "recommendation": "APPROVE_WITH_CONDITIONS",
  "overall_risk": "MODERATE",
  "key_findings": [
    "Finding 1 that combines multiple perspectives",
    "Finding 2",
    "Finding 3"
  ],
  "conditions": [
    "Condition 1 if APPROVE_WITH_CONDITIONS",
    "Condition 2"
  ],
  "alternative_approaches": [
    "Alternative 1",
    "Alternative 2"
  ],
  "summary": "Executive summary here...",
  "detailed_reasoning": "Full synthesis of all three challenges...",
  "confidence_score": 0.8
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

        # Build decision
        decision = {
            "timestamp": datetime.now(UTC).isoformat(),
            "decision_id": str(uuid.uuid4()),
            "idea_id": scope_challenge.get("idea_id"),
            "idea_title": idea_title,
            "scope_challenge_id": scope_challenge.get("challenge_id"),
            "time_challenge_id": time_challenge.get("challenge_id"),
            "cost_challenge_id": cost_challenge.get("challenge_id"),
            "recommendation": analysis.get("recommendation", "RECONSIDER"),
            "overall_risk": analysis.get("overall_risk", "MODERATE"),
            "key_findings": analysis.get("key_findings", []),
            "conditions": analysis.get("conditions", []),
            "alternative_approaches": analysis.get("alternative_approaches", []),
            "summary": analysis.get("summary", ""),
            "detailed_reasoning": analysis.get("detailed_reasoning", ""),
            "confidence_score": analysis.get("confidence_score", 0.7),
            "status": "PENDING_APPROVAL"
        }

        return decision

    except json.JSONDecodeError as e:
        print(f"   ⚠️  Failed to parse Claude response as JSON: {e}")
        print(f"   Response: {response[:200]}...")
        # Return a fallback decision
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "decision_id": str(uuid.uuid4()),
            "idea_id": scope_challenge.get("idea_id"),
            "idea_title": idea_title,
            "scope_challenge_id": scope_challenge.get("challenge_id"),
            "time_challenge_id": time_challenge.get("challenge_id"),
            "cost_challenge_id": cost_challenge.get("challenge_id"),
            "recommendation": "RECONSIDER",
            "overall_risk": "HIGH",
            "key_findings": ["Decision synthesis failed to parse"],
            "conditions": [],
            "alternative_approaches": [],
            "summary": "Failed to generate decision. Manual review required.",
            "detailed_reasoning": "Decision analysis failed to parse. Manual review recommended.",
            "confidence_score": 0.3,
            "status": "PENDING_APPROVAL"
        }


def save_decision_to_file(decision):
    """Save decision to dry-run output file."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"
    output_dir.mkdir(exist_ok=True)

    filename = f"decision-{decision['decision_id']}.json"
    output_file = output_dir / filename

    with open(output_file, 'w') as f:
        json.dump(decision, f, indent=2)

    print(f"   💾 Saved to {filename}")


def publish_decision(decision, dry_run=False):
    """Publish decision to Kafka topic or file."""
    if dry_run:
        save_decision_to_file(decision)
        return True

    # Kafka publishing logic (for future full mode)
    schema_str = get_schema_string("decision")
    producer, serializer = create_avro_producer(schema_str)

    success = produce_message(
        producer,
        serializer,
        "agent-state-decisions",
        decision["idea_id"],
        decision
    )

    if success:
        print("   ✅ Decision published successfully!")
    else:
        print("   ❌ Failed to publish decision")

    return success


def run_decision_agent(dry_run=False):
    """Main decision agent execution."""
    print("\n" + "=" * 60)
    print("DECISION AGENT - Shark Tank Panel Decision")
    print("=" * 60)

    # Load challenges
    if dry_run:
        # Dry-run: Load from files
        idea_ids = load_all_idea_ids()
        if not idea_ids:
            print("\n⚠️  No challenges found to synthesize")
            return []

        print(f"\n1. Synthesizing decisions for {len(idea_ids)} ideas...")

        decisions = []
        for i, idea_id in enumerate(idea_ids, 1):
            # Load all three challenges
            challenges = load_challenges_from_files(idea_id)

            if not all(challenges.values()):
                print(f"\n   [{i}/{len(idea_ids)}] ⚠️  Missing challenges for idea {idea_id[:8]}... - skipping")
                continue

            idea_title = challenges["scope"].get("idea_title")
            print(f"\n   [{i}/{len(idea_ids)}] Synthesizing: {idea_title}")

            decision = synthesize_decision(
                idea_title,
                challenges["scope"],
                challenges["time"],
                challenges["cost"]
            )
            decisions.append(decision)

            print(f"      Recommendation: {decision['recommendation']}")
            print(f"      Overall Risk: {decision['overall_risk']}")
            print(f"      Key Findings: {len(decision['key_findings'])}")

            # Publish the decision
            publish_decision(decision, dry_run=dry_run)
    else:
        # Production: Load from Kafka
        print("\n1. Loading challenges from Kafka...")
        challenges_by_idea = load_challenges_from_kafka()

        if not challenges_by_idea:
            print("\n⚠️  No challenges found to synthesize")
            return []

        print(f"\n2. Synthesizing decisions for {len(challenges_by_idea)} ideas...")

        decisions = []
        for i, (idea_id, challenges) in enumerate(challenges_by_idea.items(), 1):
            idea_title = challenges["scope"].get("idea_title")
            print(f"\n   [{i}/{len(challenges_by_idea)}] Synthesizing: {idea_title}")

            decision = synthesize_decision(
                idea_title,
                challenges["scope"],
                challenges["time"],
                challenges["cost"]
            )
            decisions.append(decision)

            print(f"      Recommendation: {decision['recommendation']}")
            print(f"      Overall Risk: {decision['overall_risk']}")
            print(f"      Key Findings: {len(decision['key_findings'])}")

            # Publish the decision
            publish_decision(decision, dry_run=dry_run)

    print("\n" + "=" * 60)
    print(f"DECISION AGENT COMPLETE - Generated {len(decisions)} decisions")
    print("=" * 60 + "\n")

    return decisions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Decision Agent - Synthesizes scope, time, and cost challenges"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (read/write files instead of Kafka)"
    )
    args = parser.parse_args()

    run_decision_agent(dry_run=args.dry_run)
