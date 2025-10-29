#!/usr/bin/env python3
"""
Human Solution Approval Interface

Interactive CLI for reviewing and approving/rejecting AI-generated solution designs
after the Solution Agent has created technical specifications.

This is a human-in-the-loop checkpoint before moving to Implementation.

Actions:
- [a] Approve - Proceed to implementation
- [r] Reject - Send back for redesign
- [v] Revision - Request changes to solution
- [s] Skip - Move to next solution
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
    """Print header for the solution approval interface."""
    print("\n" + "=" * 80)
    print(" " * 15 + "SOLUTION APPROVAL INTERFACE")
    print("=" * 80)


def print_solution(solution, index, total):
    """Pretty print a solution for review."""
    print("\n" + "=" * 80)
    print(f"SOLUTION #{index}: {solution.get('idea_title')}")
    print("=" * 80)
    print()
    print(f"📍 Solution ID: {solution.get('solution_id')}")
    print(f"🎯 Idea ID: {solution.get('idea_id')}")
    print(f"📊 Status: {solution.get('status')}")
    print(f"🎯 Confidence: {solution.get('confidence_score'):.0%}")
    print()

    print("🏗️  TECHNICAL APPROACH:")
    print(f"   {solution.get('technical_approach')}")
    print()

    print(f"⚙️  PROCESSING ENGINE: {solution.get('processing_engine')}")
    print(f"   Rationale: {solution.get('processing_rationale')}")
    print()

    new_topics = solution.get('new_topics', [])
    if new_topics:
        print(f"📋 NEW TOPICS ({len(new_topics)}):")
        for topic in new_topics:
            print(f"   • {topic.get('name')} ({topic.get('partitions')} partitions)")
            print(f"     {topic.get('description')}")
        print()

    schemas = solution.get('schemas', [])
    if schemas:
        print(f"📐 SCHEMAS ({len(schemas)}):")
        for schema in schemas:
            print(f"   • {schema.get('subject')}")
            print(f"     {schema.get('description')}")
        print()

    queries = solution.get('query_specifications', [])
    if queries:
        print(f"🔍 QUERY SPECIFICATIONS ({len(queries)}):")
        for query in queries:
            print(f"   • {query.get('name')} ({query.get('type')})")
            print(f"     {query.get('description')}")
        print()

    infra = solution.get('infrastructure_requirements', {})
    print("💻 INFRASTRUCTURE REQUIREMENTS:")
    print(f"   Flink Compute Pool: {'Yes' if infra.get('compute_pool_required') else 'No'}")
    print(f"   ksqlDB Cluster: {'Yes' if infra.get('ksqldb_cluster_required') else 'No'}")
    connectors = infra.get('connectors_required', [])
    if connectors:
        # Handle both string and dict formats
        connector_names = []
        for conn in connectors:
            if isinstance(conn, str):
                connector_names.append(conn)
            elif isinstance(conn, dict):
                connector_names.append(conn.get('type') or conn.get('name') or str(conn))
            else:
                connector_names.append(str(conn))
        print(f"   Connectors: {', '.join(connector_names)}")
    if infra.get('estimated_csu_hours'):
        print(f"   Estimated CSU Hours/month: {infra.get('estimated_csu_hours')}")
    if infra.get('additional_notes'):
        print(f"   Notes: {infra.get('additional_notes')}")
    print()

    gov = solution.get('data_governance', {})
    print("🔐 DATA GOVERNANCE:")
    print(f"   Owner: {gov.get('owner', 'N/A')}")
    print(f"   Domain: {gov.get('domain', 'N/A')}")
    print(f"   Classification: {gov.get('classification', 'N/A')}")
    print(f"   Retention: {gov.get('retention_policy', 'N/A')}")
    tags = gov.get('tags', [])
    if tags:
        print(f"   Tags: {', '.join(tags)}")
    print()

    print(f"⏱️  ESTIMATED EFFORT: {solution.get('estimated_effort_hours')} hours")
    print()

    risks = solution.get('risks_and_mitigations', [])
    if risks:
        print(f"⚠️  RISKS & MITIGATIONS ({len(risks)}):")
        for risk in risks:
            print(f"   • [{risk.get('severity')}] {risk.get('risk')}")
            print(f"     → Mitigation: {risk.get('mitigation')}")
        print()

    metrics = solution.get('success_metrics', [])
    if metrics:
        print(f"📊 SUCCESS METRICS ({len(metrics)}):")
        for metric in metrics:
            print(f"   • {metric}")
        print()

    print("🧪 TESTING STRATEGY:")
    import textwrap
    wrapped = textwrap.fill(solution.get('testing_strategy', 'N/A'), width=76, initial_indent='   ', subsequent_indent='   ')
    print(wrapped)
    print()

    print("🚀 DEPLOYMENT CONSIDERATIONS:")
    wrapped = textwrap.fill(solution.get('deployment_considerations', 'N/A'), width=76, initial_indent='   ', subsequent_indent='   ')
    print(wrapped)
    print()


def prompt_user_action(solution):
    """Prompt user for action on this solution."""
    choices = {
        'a': 'Approve - Proceed to implementation',
        'r': 'Reject - Solution needs complete redesign',
        'v': 'Request Revision - Needs changes',
        's': 'Skip - Review later',
        'q': 'Quit - Exit approval'
    }
    return ask_choice("What would you like to do with this solution?", choices)


def apply_action(solution, action, dry_run=False):
    """Apply the user's action to the solution."""
    if action == 'a':
        # Approve
        solution['status'] = 'APPROVED'
        print_success("Solution APPROVED - Moving to implementation phase")
        return True
    elif action == 'r':
        # Reject
        solution['status'] = 'REJECTED'
        print_error("Solution REJECTED - Requires complete redesign")
        return True
    elif action == 'v':
        # Request revision
        solution['status'] = 'REVISION_REQUESTED'
        print_warning("Solution REVISION REQUESTED - Needs changes")
        return True
    elif action == 's':
        # Skip
        print_info("Solution SKIPPED - Will review later")
        return False  # Don't save changes
    elif action == 'q':
        # Quit
        print("\n👋 Exiting approval process...")
        return None
    else:
        print_warning(f"Unknown action: {action}")
        return False


def save_solution_to_file(solution):
    """Save updated solution back to dry-run output file."""
    output_dir = Path(__file__).parent / "dry-run-output"
    output_dir.mkdir(exist_ok=True)

    filename = f"solution-{solution['solution_id']}.json"
    output_file = output_dir / filename

    with open(output_file, 'w') as f:
        json.dump(solution, f, indent=2)

    print(f"   💾 Updated {filename}")


def publish_solution(solution, dry_run=False):
    """Publish updated solution to Kafka or save to file."""
    if dry_run:
        save_solution_to_file(solution)
    else:
        # Publish to Kafka
        schema_str = get_schema_string("solution")
        producer, serializer = create_avro_producer(schema_str)

        try:
            produce_message(
                producer=producer,
                serializer=serializer,
                topic="agent-state-solutions",
                key=solution["solution_id"],
                value=solution
            )
            producer.flush()
            print_success(f"   ✅ Solution published to Kafka: agent-state-solutions")
        finally:
            # Producer cleanup handled by produce_message
            pass


def load_solutions_from_files():
    """Load all pending solutions from dry-run output files."""
    output_dir = Path(__file__).parent / "dry-run-output"
    solutions = []

    for solution_file in sorted(output_dir.glob("solution-*.json")):
        with open(solution_file, 'r') as f:
            solution = json.load(f)
            if solution.get('status') == 'PENDING_APPROVAL':
                solutions.append(solution)

    return solutions


def load_solutions_from_kafka():
    """Load all pending solutions from Kafka."""
    print("   Loading solutions from Kafka...")

    solutions = []
    schema_str = get_schema_string("solution")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"solution-approval-{datetime.now().timestamp()}"
    )
    consumer.subscribe(["agent-state-solutions"])

    try:
        timeout_ms = 5000
        while True:
            msg = consumer.poll(timeout=timeout_ms / 1000.0)
            if msg is None:
                break
            if msg.error():
                continue

            value = deserializer(msg.value(), None)
            if value and value.get('status') == 'PENDING_APPROVAL':
                solutions.append(value)
    finally:
        consumer.close()

    return solutions


def run_approval_interface(dry_run=False):
    """Run the interactive approval interface."""
    print_header()

    if dry_run:
        print("\n📁 DRY RUN MODE: Reading from and writing to files\n")
        solutions = load_solutions_from_files()
    else:
        print("\n☁️  KAFKA MODE: Reading from and writing to Kafka\n")
        solutions = load_solutions_from_kafka()

    if not solutions:
        print_info("No pending solutions found for approval.")
        return

    print(f"Found {len(solutions)} solution(s) pending approval\n")

    approved_count = 0
    rejected_count = 0
    revision_count = 0

    for i, solution in enumerate(solutions, 1):
        print_solution(solution, i, len(solutions))

        while True:
            action = prompt_user_action(solution)
            result = apply_action(solution, action, dry_run)

            if result is None:  # Quit
                break
            elif result:  # Action applied successfully
                publish_solution(solution, dry_run)

                if solution.get('status') == 'APPROVED':
                    approved_count += 1
                elif solution.get('status') == 'REJECTED':
                    rejected_count += 1
                elif solution.get('status') == 'REVISION_REQUESTED':
                    revision_count += 1

                break
            # If result is False, ask again

        if action == 'q':
            break

    # Print summary
    print("\n" + "=" * 80)
    print("APPROVAL SUMMARY")
    print("=" * 80)
    print(f"✅ Approved: {approved_count}")
    print(f"❌ Rejected: {rejected_count}")
    print(f"🔄 Revision Requested: {revision_count}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Human Solution Approval Interface - Review and approve AI-generated solutions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read from files instead of Kafka (for testing)"
    )

    args = parser.parse_args()

    try:
        run_approval_interface(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  Approval process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
