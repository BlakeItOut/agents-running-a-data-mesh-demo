#!/usr/bin/env python3
"""
Current State Prompt Agent

Consumes from three pre-current-state topics:
  - agent-state-deployment
  - agent-state-usage
  - agent-state-metrics

Uses Claude to synthesize them into a coherent summary, then publishes
to agent-state-current topic.

This aggregated state becomes the input to the Learning Prompt agent.
"""

import argparse
import json
import sys
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
from common.claude_utils import synthesize_state


def load_from_files():
    """
    Load state from dry-run output files instead of Kafka.
    """
    print("\n1. Loading from dry-run output files...")

    output_dir = Path(__file__).parent.parent / "dry-run-output"

    # Deployment State
    print("   - deployment-state.json...")
    deployment_file = output_dir / "deployment-state.json"
    if deployment_file.exists():
        with open(deployment_file, 'r') as f:
            deployment_state = json.load(f)
        print("      ✅ Loaded")
    else:
        print("      ⚠️  File not found!")
        deployment_state = {}

    # Usage State
    print("   - usage-state.json...")
    usage_file = output_dir / "usage-state.json"
    if usage_file.exists():
        with open(usage_file, 'r') as f:
            usage_state = json.load(f)
        print("      ✅ Loaded")
    else:
        print("      ⚠️  File not found!")
        usage_state = {}

    # Metrics State
    print("   - metrics-state.json...")
    metrics_file = output_dir / "metrics-state.json"
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics_state = json.load(f)
        print("      ✅ Loaded")
    else:
        print("      ⚠️  File not found!")
        metrics_state = {}

    return deployment_state, usage_state, metrics_state


def consume_pre_current_state_topics(dry_run=False):
    """
    Consume latest messages from the three pre-current-state topics.
    In dry-run mode, reads from files instead of Kafka.

    Since these are compacted topics, we only need the latest message from each.
    """
    if dry_run:
        return load_from_files()

    print("\n1. Consuming from pre-current-state topics...")

    # Deployment State
    print("   - agent-state-deployment...")
    deployment_schema = get_schema_string("deployment-state")
    deployment_consumer, deployment_deserializer = create_avro_consumer(
        deployment_schema,
        group_id="current-state-prompt-deployment"
    )
    deployment_state = consume_latest_message(
        deployment_consumer,
        deployment_deserializer,
        "agent-state-deployment",
        timeout=5.0
    )

    if not deployment_state:
        print("      ⚠️  No deployment state found!")
        deployment_state = {}

    # Usage State
    print("   - agent-state-usage...")
    usage_schema = get_schema_string("usage-state")
    usage_consumer, usage_deserializer = create_avro_consumer(
        usage_schema,
        group_id="current-state-prompt-usage"
    )
    usage_state = consume_latest_message(
        usage_consumer,
        usage_deserializer,
        "agent-state-usage",
        timeout=5.0
    )

    if not usage_state:
        print("      ⚠️  No usage state found!")
        usage_state = {}

    # Metrics State
    print("   - agent-state-metrics...")
    metrics_schema = get_schema_string("metrics-state")
    metrics_consumer, metrics_deserializer = create_avro_consumer(
        metrics_schema,
        group_id="current-state-prompt-metrics"
    )
    metrics_state = consume_latest_message(
        metrics_consumer,
        metrics_deserializer,
        "agent-state-metrics",
        timeout=5.0
    )

    if not metrics_state:
        print("      ⚠️  No metrics state found!")
        metrics_state = {}

    print("   ✅ Consumed all pre-current-state topics")

    return deployment_state, usage_state, metrics_state


def create_current_state_snapshot(deployment, usage, metrics, claude_synthesis):
    """
    Create aggregated current state snapshot.

    Args:
        deployment: Deployment state data
        usage: Usage state data
        metrics: Metrics state data
        claude_synthesis: Dictionary with 'summary' and 'observations' from Claude

    Returns:
        CurrentState dict matching Avro schema
    """
    timestamp = datetime.now(UTC).isoformat()

    # Create snapshot summaries
    deployment_snapshot = {
        "timestamp": deployment.get("timestamp", timestamp),
        "cluster_id": deployment.get("cluster_id", "unknown"),
        "total_topics": len(deployment.get("topics", [])),
        "total_schemas": len(deployment.get("schemas", [])),
        "total_connectors": len(deployment.get("connectors", [])),
        "domain_count": len(deployment.get("domains", {}))
    }

    usage_snapshot = {
        "timestamp": usage.get("timestamp", timestamp),
        "consumer_groups": usage.get("consumer_groups", 0),
        "active_consumers": usage.get("active_consumers", 0),
        "idle_topic_count": len(usage.get("idle_topics", []))
    }

    metrics_snapshot = {
        "timestamp": metrics.get("timestamp", timestamp),
        "total_throughput_mbps": metrics.get("total_throughput_mbps", 0.0),
        "avg_latency_ms": metrics.get("avg_latency_ms", 0.0),
        "error_rate": metrics.get("error_rate", 0.0),
        "topics_with_lag_count": len(metrics.get("topics_with_lag", []))
    }

    current_state = {
        "timestamp": timestamp,
        "deployment": deployment_snapshot,
        "usage": usage_snapshot,
        "metrics": metrics_snapshot,
        "summary": claude_synthesis.get("summary", "No synthesis available"),
        "notable_observations": claude_synthesis.get("observations", [])
    }

    return current_state


def run_current_state_prompt(dry_run=False):
    """Main current state prompt agent logic"""
    print("=" * 60)
    print("CURRENT STATE PROMPT AGENT" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    # Step 1: Consume from pre-current-state topics or load from files
    deployment, usage, metrics = consume_pre_current_state_topics(dry_run=dry_run)

    # Step 2: Use Claude to synthesize
    print("\n2. Synthesizing state with Claude...")
    try:
        claude_synthesis = synthesize_state(deployment, usage, metrics)
        print("   ✅ Synthesis complete")
        print(f"\n   Summary: {claude_synthesis.get('summary', 'N/A')}")
        print(f"   Observations: {len(claude_synthesis.get('observations', []))}")

    except Exception as e:
        print(f"   ⚠️  Claude synthesis failed: {e}")
        print("   Using fallback synthesis...")
        claude_synthesis = {
            "summary": "Automated synthesis unavailable. Platform has basic deployment state.",
            "observations": []
        }

    # Step 3: Create aggregated current state
    print("\n3. Creating current state snapshot...")
    current_state = create_current_state_snapshot(
        deployment, usage, metrics, claude_synthesis
    )

    # Step 4: Publish to agent-state-current or save to file
    print("\n4. Publishing current state...")
    if dry_run:
        # Dry run: save to file
        output_dir = Path(__file__).parent.parent / "dry-run-output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "current-state.json"

        with open(output_file, 'w') as f:
            json.dump(current_state, f, indent=2)

        print(f"   💾 Dry run: Saved to {output_file}")
        print(f"   📊 Summary: {current_state['deployment']['total_topics']} topics, "
              f"{current_state['deployment']['domain_count']} domains")
    else:
        # Normal mode: publish to Kafka
        try:
            schema_str = get_schema_string("current-state")
            producer, serializer = create_avro_producer(schema_str)

            produce_message(
                producer=producer,
                serializer=serializer,
                topic="agent-state-current",
                key="data-mesh-cluster",
                value=current_state
            )

            print("   ✅ Current state published to Kafka successfully!")

        except Exception as e:
            print(f"   ❌ Failed to publish: {e}")
            raise

    print("\n" + "=" * 60)
    print("CURRENT STATE PROMPT COMPLETE")
    print("=" * 60)

    return current_state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Current State Prompt Agent - Synthesizes monitoring states with Claude")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run mode: read from files and save output to file instead of using Kafka")
    args = parser.parse_args()

    result = run_current_state_prompt(dry_run=args.dry_run)

    # Print summary
    print(f"\nCurrent State Summary:")
    print(f"  Topics: {result['deployment']['total_topics']}")
    print(f"  Domains: {result['deployment']['domain_count']}")
    print(f"  Consumer Groups: {result['usage']['consumer_groups']}")
    print(f"  Throughput: {result['metrics']['total_throughput_mbps']} MB/s")
    print(f"\n  {result['summary']}")
