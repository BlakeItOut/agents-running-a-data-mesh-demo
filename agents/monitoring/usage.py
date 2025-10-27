#!/usr/bin/env python3
"""
Usage Agent

Generates synthetic usage state data and publishes to agent-state-usage topic.
In production, this would track actual consumer groups and consumption patterns.

For now, generates realistic synthetic data since there are no active consumers yet.
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


def generate_synthetic_usage_state():
    """
    Generate synthetic usage state showing active cluster usage.

    Simulates a realistic production environment with multiple consumer groups
    actively processing data from various domains.
    """
    timestamp = datetime.now(UTC).isoformat()

    # Simulate realistic consumer groups across different domains
    consumer_groups = [
        "analytics-clickstream-processor",
        "fraud-detection-transactions",
        "fleet-realtime-monitoring",
        "gaming-analytics-pipeline",
        "ecommerce-order-processor",
        "insurance-claims-analyzer",
        "data-warehouse-sync"
    ]

    # Top topics by consumption (messages/sec)
    top_topics = [
        {"topic": "clickstream", "messages_per_sec": 1247, "consumer_lag": 125},
        {"topic": "transactions", "messages_per_sec": 856, "consumer_lag": 0},
        {"topic": "fleet_mgmt_location", "messages_per_sec": 723, "consumer_lag": 45},
        {"topic": "gaming_player_activity", "messages_per_sec": 612, "consumer_lag": 203},
        {"topic": "orders", "messages_per_sec": 445, "consumer_lag": 12},
        {"topic": "stock_trades", "messages_per_sec": 389, "consumer_lag": 0},
        {"topic": "insurance_customer_activity", "messages_per_sec": 267, "consumer_lag": 88},
        {"topic": "shoes", "messages_per_sec": 198, "consumer_lag": 0},
        {"topic": "pageviews", "messages_per_sec": 156, "consumer_lag": 34},
        {"topic": "users", "messages_per_sec": 89, "consumer_lag": 0}
    ]

    # A few topics remain idle (recently added or low priority)
    idle_topics = [
        "pizza_orders_cancelled",
        "device_information",
        "syslog_logs"
    ]

    usage_state = {
        "timestamp": timestamp,
        "consumer_groups": len(consumer_groups),
        "active_consumers": 24,  # Multiple consumers across the 7 groups
        "top_topics_by_consumption": top_topics,
        "idle_topics": idle_topics
    }

    return usage_state


def run_usage_agent(dry_run=False):
    """Main usage agent logic"""
    print("=" * 60)
    print("USAGE AGENT (Synthetic Data)" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    print("\n1. Generating synthetic usage state...")
    usage_state = generate_synthetic_usage_state()

    print(f"   Consumer Groups: {usage_state['consumer_groups']}")
    print(f"   Active Consumers: {usage_state['active_consumers']}")
    print(f"   Top Consumed Topics: {len(usage_state['top_topics_by_consumption'])}")
    print(f"   Idle Topics: {len(usage_state['idle_topics'])}")

    # Publish to Kafka or save to file
    print("\n2. Publishing usage state...")
    if dry_run:
        # Dry run: save to file
        output_dir = Path(__file__).parent.parent / "dry-run-output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "usage-state.json"

        with open(output_file, 'w') as f:
            json.dump(usage_state, f, indent=2)

        print(f"   💾 Dry run: Saved to {output_file}")
    else:
        # Normal mode: publish to Kafka
        try:
            schema_str = get_schema_string("usage-state")
            producer, serializer = create_avro_producer(schema_str)

            produce_message(
                producer=producer,
                serializer=serializer,
                topic="agent-state-usage",
                key="data-mesh-cluster",
                value=usage_state
            )

            print("   ✅ Usage state published to Kafka successfully!")

        except Exception as e:
            print(f"   ❌ Failed to publish: {e}")
            raise

    print("\n" + "=" * 60)
    print("USAGE AGENT COMPLETE")
    print("=" * 60)

    return usage_state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Usage Agent - Generates synthetic usage metrics")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run mode: save output to file instead of publishing to Kafka")
    args = parser.parse_args()

    result = run_usage_agent(dry_run=args.dry_run)
    print(f"\nSynthetic Usage State: {result['consumer_groups']} groups, {result['active_consumers']} consumers")
