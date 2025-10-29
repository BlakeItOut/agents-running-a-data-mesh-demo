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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import agent modules
sys.path.insert(0, str(Path(__file__).parent))

from monitoring.deployment import run_deployment_agent
from monitoring.usage import run_usage_agent
from monitoring.metrics import run_metrics_agent
from ideation.current_state import run_current_state
from ideation.learning import run_learning_agent
from human_refinement import run_human_refinement
from evaluation.scope import run_scope_agent
from evaluation.time import run_time_agent
from evaluation.cost import run_cost_agent
from evaluation.decision import run_decision_agent
from human_approval import run_human_approval
from solution.solution import run_agent as run_solution_agent
from implementation.implementation import run_agent as run_implementation_agent
from human_solution_approval import run_approval_interface as run_solution_approval


def print_header(dry_run=False, include_learning=False, include_evaluation=False, include_solution=False):
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
    if include_learning:
        print("  5. Run Learning Agent (generates data product ideas)")
    if include_evaluation:
        print("  6. Run Evaluation Agents (Scope, Time, Cost)")
        print("  7. Run Decision Agent (synthesize evaluation)")
    if include_solution:
        print("  8. Run Solution Agent (design technical solutions)")
        print("  9. Run Implementation Agent (generate code artifacts)")
    print("\n" + "=" * 70 + "\n")


def print_step(step_num: int, step_name: str):
    """Print step header"""
    print("\n" + "-" * 70)
    print(f"STEP {step_num}: {step_name}")
    print("-" * 70 + "\n")


def pause_for_user(step_name):
    """Pause and wait for user to continue"""
    print(f"\n{'─' * 70}")
    print(f"✅ {step_name} complete!")
    print("Press Enter to continue to next step...")
    print('─' * 70)
    input()


async def run_bootstrap(dry_run=False, include_learning=False, include_evaluation=False, include_solution=False, interactive=False, pause_between_steps=False):
    """Main bootstrap orchestration"""
    print_header(dry_run=dry_run, include_learning=include_learning, include_evaluation=include_evaluation, include_solution=include_solution)

    # Clean dry-run output directory for fresh demo runs
    if dry_run:
        output_dir = Path(__file__).parent / "dry-run-output"
        if output_dir.exists():
            # Remove all JSON files from previous runs
            for json_file in output_dir.glob("*.json"):
                json_file.unlink()
            print(f"🧹 Cleaned dry-run-output directory for fresh run\n")

    try:
        # Step 1: Deployment Agent (async, uses MCP)
        print_step(1, "Deployment Agent")
        start_time = time.time()
        deployment_result = await run_deployment_agent(dry_run=dry_run)
        print(f"\n⏱️  Deployment Agent completed in {time.time() - start_time:.2f}s")

        if pause_between_steps:
            pause_for_user("Deployment Agent")

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

        if pause_between_steps:
            pause_for_user("Usage Agent")

        time.sleep(0.5 if dry_run else 2)

        # Step 3: Metrics Agent (sync)
        print_step(3, "Metrics Agent")
        start_time = time.time()
        metrics_result = run_metrics_agent(dry_run=dry_run)
        print(f"\n⏱️  Metrics Agent completed in {time.time() - start_time:.2f}s")

        if pause_between_steps:
            pause_for_user("Metrics Agent")

        time.sleep(0.5 if dry_run else 2)

        # Step 4: Current State (sync, uses Claude)
        print_step(4, "Current State Agent")
        start_time = time.time()
        current_state_result = run_current_state(dry_run=dry_run)
        print(f"\n⏱️  Current State completed in {time.time() - start_time:.2f}s")

        if pause_between_steps:
            pause_for_user("Current State Agent")

        # Step 5 (Optional): Learning Agent
        learning_result = None
        if include_learning:
            time.sleep(0.5 if dry_run else 2)
            print_step(5, "Learning Agent")
            start_time = time.time()
            learning_result = run_learning_agent(dry_run=dry_run)
            print(f"\n⏱️  Learning Agent completed in {time.time() - start_time:.2f}s")

            if pause_between_steps:
                pause_for_user("Learning Agent")

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

        if learning_result:
            print(f"\n💡 Ideas Generated: {len(learning_result)}")
            if learning_result:
                print("\n📋 Generated Data Product Ideas:")
                for i, idea in enumerate(learning_result[:3], 1):
                    print(f"  {i}. {idea['title']} ({idea['domain']})")
                if len(learning_result) > 3:
                    print(f"  ... and {len(learning_result) - 3} more")

        # Step 6 (Optional): Human Refinement
        refinement_done = False
        if interactive and learning_result:
            print("\n" + "=" * 70)
            print("LAUNCHING HUMAN REFINEMENT INTERFACE")
            print("=" * 70)
            print("\nReview and approve/reject the generated ideas...")
            if not pause_between_steps:
                print("Press Enter to continue...")
                input()

            run_human_refinement(dry_run=dry_run, stop_after_first=include_evaluation)
            refinement_done = True

            print("\n" + "=" * 70)
            print("HUMAN REFINEMENT COMPLETE")
            print("=" * 70)

            if pause_between_steps:
                pause_for_user("Human Refinement")

        # Phase 3: Evaluation Layer (Iron Triangle)
        evaluation_results = None
        if include_evaluation and (refinement_done or not interactive):
            time.sleep(0.5 if dry_run else 2)

            # Step 6/7: Scope Agent
            print_step(6, "Scope Agent (Complexity Analysis)")
            start_time = time.time()
            scope_result = run_scope_agent(dry_run=dry_run, limit_one=interactive)
            print(f"\n⏱️  Scope Agent completed in {time.time() - start_time:.2f}s")

            if pause_between_steps:
                pause_for_user("Scope Agent")

            time.sleep(0.5 if dry_run else 1)

            # Step 7/8: Time Agent
            print_step(7, "Time Agent (Timeline Analysis)")
            start_time = time.time()
            time_result = run_time_agent(dry_run=dry_run, limit_one=interactive)
            print(f"\n⏱️  Time Agent completed in {time.time() - start_time:.2f}s")

            if pause_between_steps:
                pause_for_user("Time Agent")

            time.sleep(0.5 if dry_run else 1)

            # Step 8/9: Cost Agent
            print_step(8, "Cost Agent (Budget Analysis)")
            start_time = time.time()
            cost_result = run_cost_agent(dry_run=dry_run, limit_one=interactive)
            print(f"\n⏱️  Cost Agent completed in {time.time() - start_time:.2f}s")

            if pause_between_steps:
                pause_for_user("Cost Agent")

            time.sleep(0.5 if dry_run else 1)

            # Step 9/10: Decision Agent
            print_step(9, "Decision Agent (Shark Tank Panel)")
            start_time = time.time()
            decision_result = run_decision_agent(dry_run=dry_run)
            print(f"\n⏱️  Decision Agent completed in {time.time() - start_time:.2f}s")

            if pause_between_steps:
                pause_for_user("Decision Agent")

            evaluation_results = {
                "scope": scope_result,
                "time": time_result,
                "cost": cost_result,
                "decisions": decision_result
            }

            # Step 10/11 (Optional): Human Approval
            if interactive and decision_result:
                print("\n" + "=" * 70)
                print("LAUNCHING HUMAN APPROVAL INTERFACE")
                print("=" * 70)
                print("\nReview and approve/reject the final decisions...")
                if not pause_between_steps:
                    print("Press Enter to continue...")
                    input()

                run_human_approval(dry_run=dry_run)

                print("\n" + "=" * 70)
                print("HUMAN APPROVAL COMPLETE")
                print("=" * 70)

        # Phase 4: Solution & Implementation Layer
        solution_results = None
        approval_done = False
        if include_solution and (evaluation_results or not interactive):
            time.sleep(0.5 if dry_run else 2)

            # Step 10/11: Solution Agent
            print_step(10, "Solution Agent (Technical Design)")
            start_time = time.time()
            solution_result = run_solution_agent(dry_run=dry_run, use_claude=True)
            print(f"\n⏱️  Solution Agent completed in {time.time() - start_time:.2f}s")

            if pause_between_steps:
                pause_for_user("Solution Agent")

            # Step 11/12 (Optional): Human Solution Approval
            if interactive:
                print("\n" + "=" * 70)
                print("LAUNCHING SOLUTION APPROVAL INTERFACE")
                print("=" * 70)
                print("\nReview and approve/reject the solution designs...")
                if not pause_between_steps:
                    print("Press Enter to continue...")
                    input()

                run_solution_approval(dry_run=dry_run, stop_after_first=True)
                approval_done = True

                print("\n" + "=" * 70)
                print("SOLUTION APPROVAL COMPLETE")
                print("=" * 70)

                if pause_between_steps:
                    pause_for_user("Solution Approval")

            # Step 12/13: Implementation Agent
            if approval_done or not interactive:
                time.sleep(0.5 if dry_run else 2)

                print_step(11 if not interactive else 12, "Implementation Agent (Code Generation)")
                start_time = time.time()
                implementation_result = run_implementation_agent(dry_run=dry_run, use_claude=True)
                print(f"\n⏱️  Implementation Agent completed in {time.time() - start_time:.2f}s")

                if pause_between_steps:
                    pause_for_user("Implementation Agent")

                solution_results = {
                    "solutions": solution_result if solution_result else [],
                    "implementations": implementation_result if implementation_result else []
                }

        print("\n📍 Next Steps:")
        if not include_learning:
            print("  - Run with Learning Agent to generate ideas:")
            print("    python bootstrap.py" + (" --dry-run" if dry_run else ""))
        elif not interactive and learning_result:
            print("  - Review ideas with human refinement:")
            print("    python human_refinement.py" + (" --dry-run" if dry_run else ""))
            print("  OR run interactively next time:")
            print("    python bootstrap.py --interactive" + (" --dry-run" if dry_run else ""))
        elif not include_evaluation and refinement_done:
            print("  - Run evaluation agents (Shark Tank challenge):")
            print("    python bootstrap.py --interactive --skip-learning" + (" --dry-run" if dry_run else ""))
        elif not include_solution and evaluation_results:
            print("  - Run solution and implementation agents (Phase 4):")
            print("    python bootstrap.py --interactive --skip-learning --skip-evaluation" + (" --dry-run" if dry_run else ""))
        elif solution_results:
            print("  - Phase 4 complete! Implementation artifacts generated")
            if solution_results.get('implementations'):
                print(f"  - Generated {len(solution_results.get('implementations', []))} implementation(s)")
                print("  - Review implementation files in dry-run-output/ directory" if dry_run else "  - Check agent-state-implementations topic")
        else:
            print("  - Continue through agent-flow.md architecture")
        print("\n" + "=" * 70 + "\n")

        return {
            "deployment": deployment_result,
            "usage": usage_result,
            "metrics": metrics_result,
            "current_state": current_state_result,
            "learning": learning_result,
            "evaluation": evaluation_results,
            "solution": solution_results
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
    parser.add_argument(
        "--skip-learning",
        action="store_true",
        help="Skip Learning Agent (run only monitoring agents)"
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Skip Evaluation Agents (stop after human refinement)"
    )
    parser.add_argument(
        "--skip-solution",
        action="store_true",
        help="Skip Solution & Implementation Agents (stop after decision approval)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch human refinement and approval interfaces"
    )
    parser.add_argument(
        "--pause",
        action="store_true",
        help="Pause after each step (great for demos)"
    )
    args = parser.parse_args()

    # Check for required environment variables (skip in dry-run mode for some vars)
    import os

    # Determine Claude backend
    claude_backend = os.getenv('CLAUDE_BACKEND', 'anthropic').lower()

    if args.dry_run:
        # In dry-run, only Claude API credentials are required (for synthesis)
        if claude_backend == 'bedrock':
            # Bedrock requires either BEDROCK_API_KEY or AWS_ACCESS_KEY_ID
            if not os.getenv('BEDROCK_API_KEY') and not os.getenv('AWS_ACCESS_KEY_ID'):
                print("❌ Missing required Bedrock credentials:")
                print("  - Set BEDROCK_API_KEY (base64 encoded)")
                print("  OR")
                print("  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
                print("\nNote: Also set CLAUDE_BACKEND=bedrock and AWS_REGION=us-east-1")
                sys.exit(1)
            required_vars = []  # Bedrock vars already checked above
        else:
            # Anthropic Direct API
            required_vars = ["ANTHROPIC_API_KEY"]
    else:
        # Normal mode requires all Kafka/Schema Registry credentials
        required_vars = [
            "KAFKA_BOOTSTRAP_ENDPOINT",
            "KAFKA_API_KEY",
            "KAFKA_API_SECRET",
            "SCHEMA_REGISTRY_URL",
            "SCHEMA_REGISTRY_API_KEY",
            "SCHEMA_REGISTRY_API_SECRET"
        ]

        # Add Claude backend-specific requirements
        if claude_backend == 'bedrock':
            # Bedrock requires either BEDROCK_API_KEY or AWS_ACCESS_KEY_ID
            if not os.getenv('BEDROCK_API_KEY') and not os.getenv('AWS_ACCESS_KEY_ID'):
                print("❌ Missing required Bedrock credentials:")
                print("  - Set BEDROCK_API_KEY (base64 encoded)")
                print("  OR")
                print("  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
                print("\nNote: Also set CLAUDE_BACKEND=bedrock and AWS_REGION=us-east-1")
                sys.exit(1)
        else:
            # Anthropic Direct API
            required_vars.append("ANTHROPIC_API_KEY")

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        if args.dry_run:
            if claude_backend == 'anthropic':
                print("\nNote: In dry-run mode, only ANTHROPIC_API_KEY is required for Claude synthesis.")
            print("Tip: You can also use AWS Bedrock by setting CLAUDE_BACKEND=bedrock")
        else:
            print("\nPlease set these in your environment or .env file.")
            print("Tip: Use --dry-run to test without Kafka infrastructure.")
        sys.exit(1)

    # Print backend info
    if claude_backend == 'bedrock':
        region = os.getenv('AWS_REGION', 'us-east-1')
        print(f"\n🔧 Using AWS Bedrock (region: {region}) for Claude API")
    else:
        print("\n🔧 Using Anthropic Direct API for Claude")

    # Run bootstrap (include_learning, include_evaluation, and include_solution are True by default unless --skip flags are set)
    result = asyncio.run(run_bootstrap(
        dry_run=args.dry_run,
        include_learning=not args.skip_learning,
        include_evaluation=not args.skip_evaluation,
        include_solution=not args.skip_solution,
        interactive=args.interactive,
        pause_between_steps=args.pause
    ))
