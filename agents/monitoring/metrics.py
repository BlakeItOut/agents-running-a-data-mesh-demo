#!/usr/bin/env python3
"""
Metrics Agent

Generates synthetic metrics state data and publishes to agent-state-metrics topic.
In production, this would query Confluent Cloud Metrics API for real metrics.

For now, generates realistic synthetic metrics based on 37 datagen connectors.
"""

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.kafka_utils import create_avro_producer, produce_message
from common.schema_utils import get_schema_string


def generate_synthetic_metrics_state():
    """
    Generate synthetic metrics state showing active cluster usage.

    Simulates a realistic production environment with high throughput,
    some consumer lag, and healthy but utilized infrastructure.
    """
    timestamp = datetime.now(UTC).isoformat()

    # Topics with consumer lag (from usage patterns)
    # Note: lag_messages is total lag across partitions for this consumer group
    topics_with_lag = [
        {"topic_name": "gaming_player_activity", "consumer_group": "gaming-analytics-pipeline", "lag_messages": 203},
        {"topic_name": "clickstream", "consumer_group": "analytics-clickstream-processor", "lag_messages": 125},
        {"topic_name": "insurance_customer_activity", "consumer_group": "insurance-claims-analyzer", "lag_messages": 88},
        {"topic_name": "fleet_mgmt_location", "consumer_group": "fleet-realtime-monitoring", "lag_messages": 45},
        {"topic_name": "pageviews", "consumer_group": "analytics-clickstream-processor", "lag_messages": 34},
        {"topic_name": "orders", "consumer_group": "ecommerce-order-processor", "lag_messages": 12}
    ]

    # Production-level throughput
    # Top 10 topics: ~5000 msgs/sec, avg 2KB/msg = ~10 MB/s
    # Plus remaining 27 topics at lower rates = ~15 MB/s total
    total_throughput_mbps = 15.3

    metrics_state = {
        "timestamp": timestamp,
        "total_throughput_mbps": total_throughput_mbps,
        "avg_latency_ms": 32.0,  # Low latency, healthy cluster
        "topics_with_lag": topics_with_lag,
        "error_rate": 0.002,  # 0.2% error rate (realistic for production)
        "storage_used_gb": 847.5  # Realistic storage for active 37 topics over 7 days
    }

    return metrics_state


def run_metrics_agent(dry_run=False):
    """Main metrics agent logic"""
    print("=" * 60)
    print("METRICS AGENT (Synthetic Data)" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    print("\n1. Generating synthetic metrics state...")
    metrics_state = generate_synthetic_metrics_state()

    print(f"   Throughput: {metrics_state['total_throughput_mbps']} MB/s")
    print(f"   Avg Latency: {metrics_state['avg_latency_ms']} ms")
    print(f"   Error Rate: {metrics_state['error_rate'] * 100:.1f}%")
    print(f"   Topics with Lag: {len(metrics_state['topics_with_lag'])}")
    print(f"   Storage Used: {metrics_state['storage_used_gb']} GB")

    # Publish to Kafka or save to file
    print("\n2. Publishing metrics state...")
    if dry_run:
        # Dry run: save to file
        output_dir = Path(__file__).parent.parent / "dry-run-output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "metrics-state.json"

        with open(output_file, 'w') as f:
            json.dump(metrics_state, f, indent=2)

        print(f"   💾 Dry run: Saved to {output_file}")
    else:
        # Normal mode: publish to Kafka
        try:
            schema_str = get_schema_string("metrics-state")
            producer, serializer = create_avro_producer(schema_str)

            produce_message(
                producer=producer,
                serializer=serializer,
                topic="agent-state-metrics",
                key="data-mesh-cluster",
                value=metrics_state
            )

            print("   ✅ Metrics state published to Kafka successfully!")

        except Exception as e:
            print(f"   ❌ Failed to publish: {e}")
            raise

    print("\n" + "=" * 60)
    print("METRICS AGENT COMPLETE")
    print("=" * 60)

    return metrics_state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metrics Agent - Generates synthetic system metrics")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run mode: save output to file instead of publishing to Kafka")
    args = parser.parse_args()

    result = run_metrics_agent(dry_run=args.dry_run)
    print(f"\nSynthetic Metrics: {result['total_throughput_mbps']} MB/s throughput, {result['avg_latency_ms']} ms latency")
