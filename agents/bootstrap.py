#!/usr/bin/env python3
"""
Bootstrap Script for Agent Orchestration

Runs all monitoring agents and the current state prompt agent in sequence.

Flow:
1. Deployment Agent → agent-state-deployment
2. Usage Agent → agent-state-usage
3. Metrics Agent → agent-state-metrics
4. Current State Prompt → agent-state-current (synthesizes 1-3 with Claude)

This establishes the initial "Current State" for the Learning Prompt agent.
"""

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
from ideation.current_state_prompt import run_current_state_prompt


def print_header():
    """Print bootstrap header"""
    print("\n" + "=" * 70)
    print(" " * 15 + "AGENT ORCHESTRATION BOOTSTRAP")
    print("=" * 70)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis script will:")
    print("  1. Run Deployment Agent (discovers Confluent Cloud state)")
    print("  2. Run Usage Agent (generates synthetic usage data)")
    print("  3. Run Metrics Agent (generates synthetic metrics data)")
    print("  4. Run Current State Prompt (synthesizes with Claude)")
    print("\n" + "=" * 70 + "\n")


def print_step(step_num: int, step_name: str):
    """Print step header"""
    print("\n" + "-" * 70)
    print(f"STEP {step_num}: {step_name}")
    print("-" * 70 + "\n")


async def run_bootstrap():
    """Main bootstrap orchestration"""
    print_header()

    try:
        # Step 1: Deployment Agent (async, uses MCP)
        print_step(1, "Deployment Agent")
        start_time = time.time()
        deployment_result = await run_deployment_agent()
        print(f"\n⏱️  Deployment Agent completed in {time.time() - start_time:.2f}s")

        # Brief pause to ensure Kafka commits
        print("\n⏸️  Pausing 2 seconds for Kafka topic sync...")
        time.sleep(2)

        # Step 2: Usage Agent (sync)
        print_step(2, "Usage Agent")
        start_time = time.time()
        usage_result = run_usage_agent()
        print(f"\n⏱️  Usage Agent completed in {time.time() - start_time:.2f}s")

        time.sleep(2)

        # Step 3: Metrics Agent (sync)
        print_step(3, "Metrics Agent")
        start_time = time.time()
        metrics_result = run_metrics_agent()
        print(f"\n⏱️  Metrics Agent completed in {time.time() - start_time:.2f}s")

        time.sleep(2)

        # Step 4: Current State Prompt (sync, uses Claude)
        print_step(4, "Current State Prompt Agent")
        start_time = time.time()
        current_state_result = run_current_state_prompt()
        print(f"\n⏱️  Current State Prompt completed in {time.time() - start_time:.2f}s")

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
        print("\n✅ All agent state topics are now populated!")
        print("✅ Current state is available in: agent-state-current")
        print("\n📍 Next Steps:")
        print("  - Run Learning Prompt agent to generate ideas")
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
    # Check for required environment variables
    import os
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
        print("\nPlease set these in your environment or .env file.")
        sys.exit(1)

    # Run bootstrap
    result = asyncio.run(run_bootstrap())
