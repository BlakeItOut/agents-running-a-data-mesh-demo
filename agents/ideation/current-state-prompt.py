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


def consume_pre_current_state_topics():
    """
    Consume latest messages from the three pre-current-state topics.

    Since these are compacted topics, we only need the latest message from each.
    """
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


def run_current_state_prompt():
    """Main current state prompt agent logic"""
    print("=" * 60)
    print("CURRENT STATE PROMPT AGENT")
    print("=" * 60)

    # Step 1: Consume from pre-current-state topics
    deployment, usage, metrics = consume_pre_current_state_topics()

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

    # Step 4: Publish to agent-state-current
    print("\n4. Publishing to agent-state-current topic...")
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

        print("   ✅ Current state published successfully!")

    except Exception as e:
        print(f"   ❌ Failed to publish: {e}")
        raise

    print("\n" + "=" * 60)
    print("CURRENT STATE PROMPT COMPLETE")
    print("=" * 60)

    return current_state


if __name__ == "__main__":
    result = run_current_state_prompt()

    # Print summary
    print(f"\nCurrent State Summary:")
    print(f"  Topics: {result['deployment']['total_topics']}")
    print(f"  Domains: {result['deployment']['domain_count']}")
    print(f"  Consumer Groups: {result['usage']['consumer_groups']}")
    print(f"  Throughput: {result['metrics']['total_throughput_mbps']} MB/s")
    print(f"\n  {result['summary']}")
