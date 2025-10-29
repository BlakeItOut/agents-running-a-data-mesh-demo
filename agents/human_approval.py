#!/usr/bin/env python3
"""
Human Approval Interface

Interactive CLI for reviewing and approving/rejecting AI-generated decisions
after the three evaluation agents (Scope, Time, Cost) have assessed ideas.

This is the final human-in-the-loop checkpoint before moving to Solution Design.

Actions:
- [a] Approve - Proceed to solution design
- [r] Reject - Send back to ideation
- [d] Defer - Review later
- [e] Edit - Modify decision details
- [s] Skip - Move to next decision
- [q] Quit - Exit approval process
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, UTC

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from common.kafka_utils import create_avro_consumer, create_avro_producer, produce_message
from common.schema_utils import get_schema_string
from common.interactive_utils import (
    ask_choice,
    print_success,
    print_error,
    print_warning,
    print_info
)


def print_header():
    """Print header for the human approval interface."""
    print("\n" + "=" * 80)
    print(" " * 20 + "HUMAN APPROVAL INTERFACE")
    print("=" * 80)


def print_decision(decision, index, total):
    """Pretty print a decision for review."""
    print("\n" + "=" * 80)
    print(f"DECISION #{index}: {decision.get('idea_title')}")
    print("=" * 80)
    print()
    print(f"📍 Decision ID: {decision.get('decision_id')}")
    print(f"🎯 Idea ID: {decision.get('idea_id')}")
    print(f"📊 Status: {decision.get('status')}")
    print()
    print(f"📋 RECOMMENDATION: {decision.get('recommendation')}")
    print(f"⚠️  OVERALL RISK: {decision.get('overall_risk')}")
    print(f"🎯 CONFIDENCE: {decision.get('confidence_score'):.0%}")
    print()
    print("📝 Summary:")
    print(f"   {decision.get('summary')}")
    print()
    print(f"💡 Key Findings ({len(decision.get('key_findings', []))}):")
    for finding in decision.get('key_findings', []):
        print(f"   • {finding}")
    print()

    conditions = decision.get('conditions', [])
    if conditions:
        print(f"⚙️  Conditions ({len(conditions)}):")
        for condition in conditions:
            print(f"   • {condition}")
        print()

    alternatives = decision.get('alternative_approaches', [])
    if alternatives:
        print(f"🔄 Alternative Approaches ({len(alternatives)}):")
        for alt in alternatives:
            print(f"   • {alt}")
        print()

    print("📖 Detailed Reasoning:")
    reasoning = decision.get('detailed_reasoning', '')
    # Wrap text at 76 characters
    import textwrap
    wrapped = textwrap.fill(reasoning, width=76, initial_indent='   ', subsequent_indent='   ')
    print(wrapped)
    print()


def prompt_user_action(decision):
    """Prompt user for action on this decision."""
    choices = {
        'a': 'Approve - Proceed to solution design',
        'r': 'Reject - Send back to ideation',
        'd': 'Defer - Review later',
        's': 'Skip - Review later (same as defer)',
        'q': 'Quit - Exit approval'
    }
    return ask_choice("What would you like to do with this decision?", choices)


def apply_action(decision, action, dry_run=False):
    """Apply the user's action to the decision."""
    if action == 'a':
        # Approve
        decision['status'] = 'APPROVED'
        print_success("Decision APPROVED - Moving to solution design phase")
        return True
    elif action == 'r':
        # Reject
        decision['status'] = 'REJECTED'
        print_error("Decision REJECTED - Sending back to ideation")
        return True
    elif action == 'd' or action == 's':
        # Defer/Skip
        decision['status'] = 'DEFERRED'
        print_info("Decision DEFERRED - Will review later")
        return True
    elif action == 'e':
        # Edit (not implemented)
        print_warning("Edit functionality not yet implemented")
        return False
    elif action == 'q':
        # Quit
        print("\n👋 Exiting approval process...")
        return None
    else:
        print_warning(f"Unknown action: {action}")
        return False


def save_decision_to_file(decision):
    """Save updated decision back to dry-run output file."""
    output_dir = Path(__file__).parent / "dry-run-output"
    output_dir.mkdir(exist_ok=True)

    filename = f"decision-{decision['decision_id']}.json"
    output_file = output_dir / filename

    with open(output_file, 'w') as f:
        json.dump(decision, f, indent=2)

    print(f"   💾 Updated {filename}")


def publish_decision(decision, dry_run=False):
    """Publish updated decision to Kafka or save to file."""
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
        print("   ✅ Decision published to Kafka")
    else:
        print("   ❌ Failed to publish decision")

    return success


def load_decisions_from_kafka():
    """Load decisions from Kafka topic."""
    print("\n📥 Consuming decisions from Kafka...")

    schema_str = get_schema_string("decision")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"human-approval-{datetime.now().timestamp()}"
    )

    consumer.subscribe(["agent-state-decisions"])

    decisions = []
    try:
        timeout_ms = 5000
        while True:
            msg = consumer.poll(timeout=timeout_ms / 1000.0)

            if msg is None:
                break

            if msg.error():
                continue

            value = deserializer(msg.value(), None)
            # Only load decisions that are PENDING_APPROVAL
            if value and value.get("status") == "PENDING_APPROVAL":
                decisions.append(value)

    finally:
        consumer.close()

    # Sort by timestamp (most recent first)
    if decisions and 'timestamp' in decisions[0]:
        decisions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    print(f"   ✅ Consumed {len(decisions)} decisions")
    return decisions


def load_decisions(dry_run=False):
    """Load decisions that need approval."""
    if dry_run:
        return load_decisions_from_files()
    else:
        return load_decisions_from_kafka()


def load_decisions_from_files():
    """Load decisions from dry-run output files."""
    print("\n📂 Loading decisions from dry-run output files...")

    output_dir = Path(__file__).parent / "dry-run-output"
    decisions = []

    # Find all decision files
    for decision_file in output_dir.glob("decision-*.json"):
        with open(decision_file, 'r') as f:
            decision = json.load(f)
            # Only load decisions that are PENDING_APPROVAL
            if decision.get("status") == "PENDING_APPROVAL":
                decisions.append(decision)

    print(f"   ✅ Loaded {len(decisions)} decisions")
    return decisions


def approve_decisions(decisions, dry_run=False, stop_after_first=False):
    """Interactive loop for approving decisions.

    Args:
        decisions: List of decisions to review
        dry_run: If True, write to files instead of Kafka
        stop_after_first: If True, stop after first approval/rejection (for bootstrap integration)
    """
    total = len(decisions)

    if total == 0:
        print("\n✨ No decisions pending approval!")
        return

    print(f"\n📊 {total} decisions to review\n")

    for i, decision in enumerate(decisions, 1):
        print_decision(decision, i, total)

        while True:
            action = prompt_user_action(decision)
            result = apply_action(decision, action, dry_run=dry_run)

            if result is None:
                # User wants to quit
                return
            elif result:
                # Action successful, save and move to next
                publish_decision(decision, dry_run=dry_run)
                break
            # else: action failed, ask again

        # Stop after first approval/rejection when called from bootstrap
        if stop_after_first and result:
            break

    print("\n" + "=" * 80)
    print(" " * 25 + "APPROVAL COMPLETE!")
    print("=" * 80)
    print(f"\n✅ Reviewed {total} decisions\n")


def run_human_approval(dry_run=False, stop_after_first=False):
    """Main entry point for human approval.

    Args:
        dry_run: If True, read from/write to files instead of Kafka
        stop_after_first: If True, stop after first approval/rejection (for bootstrap integration)
    """
    print_header()

    decisions = load_decisions(dry_run=dry_run)
    approve_decisions(decisions, dry_run=dry_run, stop_after_first=stop_after_first)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Human Approval - Review and approve AI-generated decisions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (read/write files instead of Kafka)"
    )
    args = parser.parse_args()

    run_human_approval(dry_run=args.dry_run)
