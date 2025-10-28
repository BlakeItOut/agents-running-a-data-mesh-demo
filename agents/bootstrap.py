#!/usr/bin/env python3
"""
Bootstrap Script for Agent Orchestration

Runs all monitoring agents and the current state agent in sequence.

Flow:
1. Deployment Agent → agent-state-deployment (or dry-run-output/deployment-state.json)
2. Usage Agent → agent-state-usage (or dry-run-output/usage-state.json)
3. Metrics Agent → agent-state-metrics (or dry-run-output/metrics-state.json)
4. Current State → agent-state-current (or dry-run-output/current-state.json)

This establishes the initial "Current State" for the Learning Agent.

Supports --dry-run mode for testing without Kafka infrastructure.
"""

import argparse
import sys
import asyncio
import time
from pathlib import Path
from datetime import datetime

# Import agent modules
sys.path.insert(0, str(Path(__file__).parent))

from monitoring.deployment import run_deployment_agent
from monitoring.usage import run_usage_agent
from monitoring.metrics import run_metrics_agent
from ideation.current_state import run_current_state


def print_header(dry_run=False):
    """Print bootstrap header"""
    print("\n" + "=" * 70)
    mode = " (DRY RUN MODE)" if dry_run else ""
    print(" " * 10 + f"AGENT ORCHESTRATION BOOTSTRAP{mode}")
    print("=" * 70)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if dry_run:
        print("\n🧪 DRY RUN MODE: Output will be saved to files, not Kafka")

    print("\nThis script will:")
    print("  1. Run Deployment Agent (discovers Confluent Cloud state)")
    print("  2. Run Usage Agent (generates synthetic usage data)")
    print("  3. Run Metrics Agent (generates synthetic metrics data)")
    print("  4. Run Current State (synthesizes with Claude)")
    print("\n" + "=" * 70 + "\n")


def print_step(step_num: int, step_name: str):
    """Print step header"""
    print("\n" + "-" * 70)
    print(f"STEP {step_num}: {step_name}")
    print("-" * 70 + "\n")


async def run_bootstrap(dry_run=False):
    """Main bootstrap orchestration"""
    print_header(dry_run=dry_run)

    try:
        # Step 1: Deployment Agent (async, uses MCP)
        print_step(1, "Deployment Agent")
        start_time = time.time()
        deployment_result = await run_deployment_agent(dry_run=dry_run)
        print(f"\n⏱️  Deployment Agent completed in {time.time() - start_time:.2f}s")

        # Brief pause to ensure Kafka commits (or file writes in dry-run)
        if not dry_run:
            print("\n⏸️  Pausing 2 seconds for Kafka topic sync...")
            time.sleep(2)
        else:
            time.sleep(0.5)  # Shorter pause in dry-run

        # Step 2: Usage Agent (sync)
        print_step(2, "Usage Agent")
        start_time = time.time()
        usage_result = run_usage_agent(dry_run=dry_run)
        print(f"\n⏱️  Usage Agent completed in {time.time() - start_time:.2f}s")

        time.sleep(0.5 if dry_run else 2)

        # Step 3: Metrics Agent (sync)
        print_step(3, "Metrics Agent")
        start_time = time.time()
        metrics_result = run_metrics_agent(dry_run=dry_run)
        print(f"\n⏱️  Metrics Agent completed in {time.time() - start_time:.2f}s")

        time.sleep(0.5 if dry_run else 2)

        # Step 4: Current State (sync, uses Claude)
        print_step(4, "Current State Agent")
        start_time = time.time()
        current_state_result = run_current_state(dry_run=dry_run)
        print(f"\n⏱️  Current State completed in {time.time() - start_time:.2f}s")

        # Final Summary
        print("\n" + "=" * 70)
        print(" " * 20 + "BOOTSTRAP COMPLETE!")
        print("=" * 70)
        print("\n📊 Final State Summary:")
        print(f"  • Topics Discovered: {deployment_result.get('topics', [])[:5]}... ({len(deployment_result.get('topics', []))} total)")
        print(f"  • Domains: {len(deployment_result.get('domains', {}))}")
        print(f"  • Consumer Groups: {usage_result.get('consumer_groups', 0)}")
        print(f"  • Throughput: {metrics_result.get('total_throughput_mbps', 0)} MB/s")

        print(f"\n💡 Claude's Summary:")
        print(f"  {current_state_result.get('summary', 'N/A')}")

        if current_state_result.get('notable_observations'):
            print(f"\n🔍 Notable Observations:")
            for i, obs in enumerate(current_state_result['notable_observations'], 1):
                print(f"  {i}. {obs}")

        print("\n" + "=" * 70)
        if dry_run:
            print("\n✅ All agent outputs saved to dry-run-output/ directory!")
            print("✅ Current state is available in: dry-run-output/current-state.json")
        else:
            print("\n✅ All agent state topics are now populated!")
            print("✅ Current state is available in: agent-state-current topic")

        print("\n📍 Next Steps:")
        print("  - Run Learning Agent to generate ideas")
        print("  - Continue through agent-flow.md architecture")
        print("\n" + "=" * 70 + "\n")

        return {
            "deployment": deployment_result,
            "usage": usage_result,
            "metrics": metrics_result,
            "current_state": current_state_result
        }

    except KeyboardInterrupt:
        print("\n\n⚠️  Bootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Bootstrap failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Bootstrap Agent Orchestration System",
        epilog="Runs all monitoring agents and current state in sequence"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: save outputs to files instead of Kafka (skips env var checks)"
    )
    args = parser.parse_args()

    # Check for required environment variables (skip in dry-run mode for some vars)
    import os

    if args.dry_run:
        # In dry-run, only Claude API key is required (for synthesis)
        required_vars = ["ANTHROPIC_API_KEY"]
    else:
        # Normal mode requires all Kafka/Schema Registry credentials
        required_vars = [
            "KAFKA_BOOTSTRAP_ENDPOINT",
            "KAFKA_API_KEY",
            "KAFKA_API_SECRET",
            "SCHEMA_REGISTRY_URL",
            "SCHEMA_REGISTRY_API_KEY",
            "SCHEMA_REGISTRY_API_SECRET",
            "ANTHROPIC_API_KEY"
        ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        if args.dry_run:
            print("\nNote: In dry-run mode, only ANTHROPIC_API_KEY is required for Claude synthesis.")
        else:
            print("\nPlease set these in your environment or .env file.")
            print("Tip: Use --dry-run to test without Kafka infrastructure.")
        sys.exit(1)

    # Run bootstrap
    result = asyncio.run(run_bootstrap(dry_run=args.dry_run))
