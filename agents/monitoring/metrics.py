#!/usr/bin/env python3
"""
Metrics Agent

Generates synthetic metrics state data and publishes to agent-state-metrics topic.
In production, this would query Confluent Cloud Metrics API for real metrics.

For now, generates realistic synthetic metrics based on 37 datagen connectors.
"""

import sys
from datetime import datetime, UTC
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.kafka_utils import create_avro_producer, produce_message
from common.schema_utils import get_schema_string


def generate_synthetic_metrics_state():
    """
    Generate synthetic metrics state.

    Estimates based on 37 datagen connectors producing 1 msg/sec each:
    - 37 messages/sec total
    - Assuming avg message size ~1KB = 0.037 MB/sec
    - Latency should be low with no consumers
    """
    timestamp = datetime.now(UTC).isoformat()

    metrics_state = {
        "timestamp": timestamp,
        "total_throughput_mbps": 0.037,  # ~37 KB/sec = 0.037 MB/sec
        "avg_latency_ms": 45.0,  # Low latency, typical for datagen
        "topics_with_lag": [],  # No consumers = no lag
        "error_rate": 0.0,  # No errors in synthetic environment
        "storage_used_gb": 2.5  # Estimated storage for 37 topics with 7-day retention
    }

    return metrics_state


def run_metrics_agent():
    """Main metrics agent logic"""
    print("=" * 60)
    print("METRICS AGENT (Synthetic Data)")
    print("=" * 60)

    print("\n1. Generating synthetic metrics state...")
    metrics_state = generate_synthetic_metrics_state()

    print(f"   Throughput: {metrics_state['total_throughput_mbps']} MB/s")
    print(f"   Avg Latency: {metrics_state['avg_latency_ms']} ms")
    print(f"   Error Rate: {metrics_state['error_rate'] * 100}%")
    print(f"   Storage Used: {metrics_state['storage_used_gb']} GB")

    # Publish to Kafka
    print("\n2. Publishing to agent-state-metrics topic...")
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

        print("   ✅ Metrics state published successfully!")

    except Exception as e:
        print(f"   ❌ Failed to publish: {e}")
        raise

    print("\n" + "=" * 60)
    print("METRICS AGENT COMPLETE")
    print("=" * 60)

    return metrics_state


if __name__ == "__main__":
    result = run_metrics_agent()
    print(f"\nSynthetic Metrics: {result['total_throughput_mbps']} MB/s throughput, {result['avg_latency_ms']} ms latency")
