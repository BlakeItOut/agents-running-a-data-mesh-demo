#!/usr/bin/env python3
"""
Implementation Agent - Implementation Layer (Phase 4)

Generates implementation artifacts for approved solutions.
Creates actual Terraform code, ksqlDB/Flink SQL queries, documentation, and PR information.

Consumes approved solutions and produces implementation artifacts.
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, UTC
from pathlib import Path
import time
import subprocess
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.kafka_utils import (
    create_avro_consumer,
    create_avro_producer,
    consume_latest_message,
    produce_message
)
from common.schema_utils import get_schema_string
from common.claude_utils import call_claude
from common.json_repair import extract_and_repair_json


def load_solution_from_file(solution_id=None):
    """Load approved solution from dry-run output files."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"

    for solution_file in output_dir.glob("solution-*.json"):
        with open(solution_file, 'r') as f:
            solution = json.load(f)
            if solution.get("status") == "APPROVED":
                if solution_id is None or solution.get("solution_id") == solution_id:
                    return solution

    return None


def load_approved_solutions_from_kafka(consume_one_only=False):
    """Load approved solutions from Kafka.

    Args:
        consume_one_only: If True, only consume one message (for demos)
    """
    print("   Loading approved solutions from Kafka...")

    approved_solutions = []

    schema_str = get_schema_string("solution")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"implementation-agent-{datetime.now().timestamp()}"
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
            if value and value.get("status") == "APPROVED":
                approved_solutions.append(value)
                if consume_one_only:
                    break
    finally:
        consumer.close()

    return approved_solutions


def generate_implementation_with_agent(solution, start_time):
    """
    Use Claude Code CLI to iteratively generate implementation artifacts.

    This spawns a Claude Code agent with full file system access (Write, Edit, Bash tools).

    Args:
        solution: The approved solution design
        start_time: Start time for tracking generation duration

    Returns:
        dict: Implementation with generated artifacts
    """
    print(f"      🤖 Using Claude Code CLI for iterative implementation generation...")

    # Check if claude CLI is available
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"      ⚠️  Claude CLI not available, falling back...")
        raise Exception("Claude CLI not found")

    # Prepare context
    idea_title = solution.get("idea_title", "Unknown")
    technical_approach = solution.get("technical_approach", "")
    processing_engine = solution.get("processing_engine", "KSQLDB")
    new_topics = solution.get("new_topics", [])
    schemas = solution.get("schemas", [])
    query_specs = solution.get("query_specifications", [])
    infrastructure = solution.get("infrastructure_requirements", {})
    governance = solution.get("data_governance", {})
    domain = governance.get("domain", "unknown")

    # Sanitize title for file names
    safe_title = idea_title.lower().replace(" ", "-").replace("/", "-")

    repo_root = Path(__file__).parent.parent.parent

    agent_prompt = f"""Generate production-ready implementation artifacts for this approved data product:

**Solution Design:**
- Title: {idea_title}
- Domain: {domain}
- Technical Approach: {technical_approach}
- Processing Engine: {processing_engine}

**New Topics:**
{json.dumps(new_topics, indent=2)}

**Schemas:**
{json.dumps(schemas, indent=2)}

**Query Specifications:**
{json.dumps(query_specs, indent=2)}

**Infrastructure:**
{json.dumps(infrastructure, indent=2)}

**Governance:**
{json.dumps(governance, indent=2)}

**Your Task:**

Use the Write tool to create these 3 files:

1. **terraform/data-products/{domain}-{safe_title}.tf**
   - Complete Terraform configuration
   - Define Kafka topics using `confluent_kafka_topic`
   - Register Avro schemas using `confluent_schema`
   - Reference: confluent_kafka_cluster.datagen_cluster, confluent_environment.datagen_env
   - Use API key: confluent_api_key.cluster_admin_api_key
   - Include ACLs if needed
   - Add outputs

2. **queries/{safe_title}.sql**
   - Complete ksqlDB/Flink SQL queries
   - CREATE STREAM and CREATE TABLE statements
   - All aggregations, joins, windows from specs
   - Production-ready, executable SQL

3. **docs/data-products/{safe_title}-README.md**
   - Complete documentation
   - Overview, architecture, usage examples
   - Deployment instructions
   - Query patterns

Make all files complete, production-ready, and deployable. Start with the Terraform file.
"""

    try:
        print(f"      Calling Claude Code CLI...")

        # Call claude CLI in non-interactive mode
        result = subprocess.run(
            [
                "claude",
                "--print",  # Non-interactive mode
                "--dangerously-skip-permissions",  # Auto-approve tool use
                "--model", "sonnet",  # Use latest Sonnet
                agent_prompt
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            print(f"      ❌ Claude CLI failed with code {result.returncode}")
            print(f"      Stderr: {result.stderr[:500]}")
            raise Exception(f"Claude CLI failed: {result.stderr}")

        print(f"      ✅ Claude Code completed generation")
        print(f"      Output: {result.stdout[:200]}...")

        # Now read back the files that were created
        artifacts = []
        terraform_resources = []

        # Check for Terraform file
        tf_file = repo_root / "terraform" / "data-products" / f"{domain}-{safe_title}.tf"
        if tf_file.exists():
            with open(tf_file, 'r') as f:
                content = f.read()
                artifacts.append({
                    "path": str(tf_file.relative_to(repo_root)),
                    "type": "TERRAFORM",
                    "content": content,
                    "description": f"Terraform configuration for {idea_title}"
                })
                print(f"      ✅ Found Terraform file: {tf_file.relative_to(repo_root)}")

        # Check for SQL queries
        sql_file = repo_root / "queries" / f"{safe_title}.sql"
        if sql_file.exists():
            with open(sql_file, 'r') as f:
                content = f.read()
                artifacts.append({
                    "path": str(sql_file.relative_to(repo_root)),
                    "type": "KSQLDB" if processing_engine == "KSQLDB" else "FLINK_SQL",
                    "content": content,
                    "description": f"{processing_engine} queries for {idea_title}"
                })
                print(f"      ✅ Found SQL file: {sql_file.relative_to(repo_root)}")

        # Check for documentation
        doc_file = repo_root / "docs" / "data-products" / f"{safe_title}-README.md"
        if doc_file.exists():
            with open(doc_file, 'r') as f:
                content = f.read()
                artifacts.append({
                    "path": str(doc_file.relative_to(repo_root)),
                    "type": "DOCUMENTATION",
                    "content": content,
                    "description": f"Documentation for {idea_title}"
                })
                print(f"      ✅ Found documentation: {doc_file.relative_to(repo_root)}")

        if not artifacts:
            print(f"      ⚠️  No artifacts found, agent may not have created files")
            print(f"      Falling back to simple generation...")
            return create_fallback_implementation(solution, start_time)

        generation_time = time.time() - start_time
        total_lines = sum(len(a["content"].split('\n')) for a in artifacts)

        # Build implementation
        implementation = {
            "timestamp": datetime.now(UTC).isoformat(),
            "implementation_id": str(uuid.uuid4()),
            "solution_id": solution.get("solution_id"),
            "idea_id": solution.get("idea_id"),
            "idea_title": idea_title,
            "artifacts": artifacts,
            "terraform_resources": terraform_resources,
            "pull_request": {
                "branch_name": f"feat/data-product-{safe_title}",
                "title": f"Add {idea_title} Data Product",
                "description": f"Implementation of {idea_title} data product generated by Implementation Agent.\n\nDomain: {domain}\nProcessing Engine: {processing_engine}",
                "base_branch": "main",
                "labels": [],
                "url": None
            },
            "deployment_plan": {
                "steps": [],
                "rollback_procedure": "terraform destroy for new resources",
                "validation_steps": ["Verify resources in Confluent Cloud UI"]
            },
            "documentation": {
                "readme_content": "",
                "usage_examples": [],
                "api_documentation": ""
            },
            "estimated_cost": {
                "monthly_usd": 100.0,
                "breakdown": []
            },
            "test_plan": [],
            "metadata": {
                "agent_version": "2.0.0-claude-code-cli",
                "generation_time_seconds": generation_time,
                "files_generated": len(artifacts),
                "total_lines_of_code": total_lines
            },
            "confidence_score": 0.95,
            "status": "GENERATED"
        }

        return implementation

    except Exception as e:
        print(f"      ❌ Claude Code CLI error: {e}")
        import traceback
        traceback.print_exc()
        print(f"      Falling back to simple generation...")
        return create_fallback_implementation(solution, start_time)


def generate_implementation(solution, use_claude=True):
    """
    Generate implementation artifacts for the solution.

    Uses Claude Code CLI for iterative, tool-enabled generation with fallback to simple generation.

    Args:
        solution: The approved solution design
        use_claude: Whether to use Claude (False for fallback)

    Returns:
        dict: Implementation with generated artifacts
    """
    print(f"\n   Generating implementation for: {solution.get('idea_title')}")

    start_time = time.time()

    if not use_claude:
        return create_fallback_implementation(solution, start_time)

    # Try Claude Code CLI approach (with full tool access)
    try:
        return generate_implementation_with_agent(solution, start_time)
    except Exception as e:
        print(f"      ⚠️  Claude Code CLI unavailable, using fallback: {e}")
        return create_fallback_implementation(solution, start_time)


def create_fallback_implementation(solution, start_time):
    """Create a basic implementation when Claude is unavailable."""
    print("      Using fallback implementation generation...")

    idea_title = solution.get("idea_title", "Unknown")
    domain = solution.get("data_governance", {}).get("domain", "unknown")
    new_topics = solution.get("new_topics", [])

    # Generate basic Terraform code
    terraform_content = f"""# {idea_title} Data Product
# Auto-generated by Implementation Agent

"""
    for topic in new_topics:
        topic_name = topic.get("name", "unknown")
        safe_name = topic_name.replace(".", "_").replace("-", "_")
        terraform_content += f"""resource "confluent_kafka_topic" "{safe_name}" {{
  kafka_cluster {{
    id = confluent_kafka_cluster.datagen_cluster.id
  }}

  rest_endpoint = confluent_kafka_cluster.datagen_cluster.rest_endpoint

  topic_name       = "{topic_name}"
  partitions_count = {topic.get("partitions", 6)}

  config = {{
    "cleanup.policy" = "delete"
    "retention.ms"   = "{topic.get("retention_ms", 604800000)}"
  }}

  credentials {{
    key    = confluent_api_key.cluster_admin_api_key.id
    secret = confluent_api_key.cluster_admin_api_key.secret
  }}
}}

"""

    readme_content = f"""# {idea_title}

Auto-generated data product.

## Topics

{json.dumps([t.get("name") for t in new_topics], indent=2)}

## Deployment

```bash
cd terraform
terraform apply
```
"""

    generation_time = time.time() - start_time

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "implementation_id": str(uuid.uuid4()),
        "solution_id": solution.get("solution_id"),
        "idea_id": solution.get("idea_id"),
        "idea_title": idea_title,
        "artifacts": [
            {
                "path": f"terraform/data-products/{domain}-{idea_title.lower().replace(' ', '-')}.tf",
                "type": "TERRAFORM",
                "content": terraform_content,
                "description": f"Terraform configuration for {idea_title}"
            },
            {
                "path": f"docs/data-products/{idea_title.lower().replace(' ', '-')}-README.md",
                "type": "DOCUMENTATION",
                "content": readme_content,
                "description": f"Documentation for {idea_title}"
            }
        ],
        "terraform_resources": [
            {
                "resource_type": "confluent_kafka_topic",
                "resource_name": t.get("name", "").replace(".", "_").replace("-", "_"),
                "description": t.get("description", "")
            } for t in new_topics
        ],
        "pull_request": {
            "branch_name": f"feat/data-product-{idea_title.lower().replace(' ', '-')}",
            "title": f"Add {idea_title} Data Product",
            "description": f"Auto-generated implementation for {idea_title} data product.",
            "base_branch": "main",
            "labels": [],
            "url": None
        },
        "deployment_plan": {
            "steps": [
                {
                    "order": 1,
                    "description": "Apply Terraform changes",
                    "command": "cd terraform && terraform apply",
                    "estimated_duration": "10 minutes"
                }
            ],
            "rollback_procedure": "terraform destroy",
            "validation_steps": ["Verify topics in Confluent Cloud UI"]
        },
        "documentation": {
            "readme_content": readme_content,
            "usage_examples": [],
            "api_documentation": ""
        },
        "estimated_cost": {
            "monthly_usd": 50.0,
            "breakdown": [
                {
                    "component": "Kafka topics",
                    "monthly_usd": 50.0
                }
            ]
        },
        "test_plan": [],
        "metadata": {
            "agent_version": "1.0.0",
            "generation_time_seconds": generation_time,
            "files_generated": 2,
            "total_lines_of_code": len(terraform_content.split('\n')) + len(readme_content.split('\n'))
        },
        "confidence_score": 0.5,
        "status": "GENERATED"
    }


def write_artifacts_to_files(implementation):
    """
    Write generated artifacts to actual files in the repository.

    Args:
        implementation: Implementation dict with artifacts

    Returns:
        List of file paths that were written
    """
    print("\n   Writing artifacts to files...")

    repo_root = Path(__file__).parent.parent.parent
    written_files = []

    for artifact in implementation.get("artifacts", []):
        file_path = repo_root / artifact["path"]

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        with open(file_path, 'w') as f:
            f.write(artifact["content"])

        written_files.append(str(file_path))
        print(f"      ✍️  {artifact['path']}")

    return written_files


def create_pull_request(implementation):
    """
    Create a git branch, commit changes, push, and create PR.

    Args:
        implementation: Implementation dict with PR info and artifacts

    Returns:
        PR URL if successful, None otherwise
    """
    print("\n   Creating Pull Request...")

    repo_root = Path(__file__).parent.parent.parent
    pr_info = implementation.get("pull_request", {})
    branch_name = pr_info.get("branch_name", f"feat/auto-{implementation['implementation_id'][:8]}")
    pr_title = pr_info.get("title", "Auto-generated data product")
    pr_description = pr_info.get("description", "Implementation generated by AI agent")
    base_branch = pr_info.get("base_branch", "main")
    labels = pr_info.get("labels", [])

    # Check if gh CLI is available
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"      Using GitHub CLI: {result.stdout.strip().split()[0]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"      ❌ GitHub CLI (gh) not found. Please install from https://cli.github.com/")
        return None

    try:
        # Get current branch to potentially return to it
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = result.stdout.strip()
        print(f"      Current branch: {current_branch}")

        # Check if we have uncommitted changes on current branch
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            print(f"      ⚠️  Warning: Uncommitted changes detected on {current_branch}")

        # Check if branch already exists (locally or remotely)
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            # Branch exists locally, delete it
            print(f"      Branch {branch_name} already exists locally, deleting...")
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=repo_root,
                check=True,
                capture_output=True
            )

        # Check if branch exists on remote
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            # Branch exists on remote
            print(f"      Branch {branch_name} exists on remote, using unique name...")
            timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            branch_name = f"{branch_name}-{timestamp}"
            print(f"      New branch name: {branch_name}")

        # Create and checkout new branch
        print(f"      Creating branch: {branch_name}")
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_root,
            check=True,
            capture_output=True
        )

        # Add files
        print(f"      Adding files...")
        files_added = []
        for artifact in implementation.get("artifacts", []):
            file_path = artifact["path"]
            print(f"         Adding: {file_path}")
            result = subprocess.run(
                ["git", "add", file_path],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True
            )
            files_added.append(file_path)

        # Verify files were staged
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = [line for line in result.stdout.strip().split('\n') if line.strip()]
        print(f"      Staged {len(staged_files)} file(s)")

        if not staged_files:
            print(f"      ⚠️  No files staged for commit - files may already be committed")
            # Return to original branch
            subprocess.run(
                ["git", "checkout", current_branch],
                cwd=repo_root,
                check=True,
                capture_output=True
            )
            return None

        # Commit
        commit_message = f"{pr_title}\n\n{pr_description}\n\nGenerated by Implementation Agent"
        print(f"      Committing changes...")
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True
        )

        # Push to remote
        print(f"      Pushing branch '{branch_name}' to remote...")
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"      ✅ Branch pushed successfully")

        # Create PR using gh CLI
        print(f"      Creating PR with gh CLI...")
        gh_command = [
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", pr_description,
            "--base", base_branch
        ]

        print(f"      Running: {' '.join(gh_command)}")
        result = subprocess.run(
            gh_command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        pr_url = result.stdout.strip()
        print(f"      ✅ PR created: {pr_url}")

        # Return to original branch
        print(f"      Returning to branch: {current_branch}")
        subprocess.run(
            ["git", "checkout", current_branch],
            cwd=repo_root,
            check=True,
            capture_output=True
        )

        return pr_url

    except subprocess.CalledProcessError as e:
        print(f"      ❌ Git/PR creation failed: {e}")
        print(f"         Command: {' '.join(e.cmd)}")
        if e.stdout:
            stdout_text = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
            if stdout_text:
                print(f"         Stdout: {stdout_text}")
        if e.stderr:
            stderr_text = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
            if stderr_text:
                print(f"         Stderr: {stderr_text}")

        # Try to return to original branch if we changed it
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False
            )
            actual_branch = result.stdout.strip() if result.returncode == 0 else None

            if actual_branch and actual_branch != current_branch:
                print(f"      Attempting to return to {current_branch}...")
                subprocess.run(
                    ["git", "checkout", current_branch],
                    cwd=repo_root,
                    check=False,
                    capture_output=True
                )
        except:
            pass

        return None
    except Exception as e:
        print(f"      ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_agent(dry_run=False, use_claude=True, limit_one=False):
    """
    Main agent logic.

    Args:
        dry_run: If True, read from files and write to files instead of Kafka
        use_claude: If True, use Claude API; otherwise use fallback logic
        limit_one: If True, only process one approved solution (for demo/interactive mode)
    """
    print("\n" + "="*80)
    print("IMPLEMENTATION AGENT - Phase 4")
    print("Generating implementation artifacts for approved solutions")
    print("="*80 + "\n")

    implementations_generated = 0

    if dry_run:
        print("📁 DRY RUN MODE: Reading from files, writing to files\n")

        # Find all approved solutions
        output_dir = Path(__file__).parent.parent / "dry-run-output"
        approved_solutions = []

        for solution_file in output_dir.glob("solution-*.json"):
            with open(solution_file, 'r') as f:
                solution = json.load(f)
                if solution.get("status") == "APPROVED":
                    approved_solutions.append(solution)

        # Limit to one if requested
        if limit_one and len(approved_solutions) > 1:
            approved_solutions = [approved_solutions[0]]

        print(f"   Found {len(approved_solutions)} approved solution(s)")

        for solution in approved_solutions:
            # Generate implementation
            implementation = generate_implementation(solution, use_claude=use_claude)

            # Write to file
            output_file = output_dir / f"implementation-{implementation['implementation_id']}.json"
            with open(output_file, 'w') as f:
                json.dump(implementation, f, indent=2)

            print(f"      ✅ Implementation generated: {output_file.name}")
            print(f"         Files: {implementation['metadata']['files_generated']}")
            print(f"         Lines of code: {implementation['metadata']['total_lines_of_code']}")
            implementations_generated += 1

    else:
        print("☁️  KAFKA MODE: Reading from and writing to Kafka topics\n")

        # Load approved solutions from Kafka
        approved_solutions = load_approved_solutions_from_kafka(consume_one_only=limit_one)

        print(f"   Found {len(approved_solutions)} approved solution(s)")

        if len(approved_solutions) == 0:
            print("\n   No approved solutions to implement.")
            return

        # Set up producer
        schema_str = get_schema_string("implementation")
        producer, serializer = create_avro_producer(schema_str)

        try:
            for solution in approved_solutions:
                # Generate implementation
                implementation = generate_implementation(solution, use_claude=use_claude)

                # Write artifacts to actual files
                written_files = write_artifacts_to_files(implementation)

                # Create PR
                pr_url = create_pull_request(implementation)

                if pr_url:
                    # Update implementation with actual PR URL
                    implementation["pull_request"]["url"] = pr_url
                    implementation["status"] = "PR_CREATED"
                    print(f"\n      🎉 PR created successfully!")
                else:
                    implementation["status"] = "GENERATED"
                    print(f"\n      ⚠️  PR creation failed, implementation saved as GENERATED")

                # Publish to Kafka
                produce_message(
                    producer=producer,
                    serializer=serializer,
                    topic="agent-state-implementations",
                    key=implementation["implementation_id"],
                    value=implementation
                )

                print(f"\n      ✅ Implementation published to Kafka")
                print(f"         Files: {implementation['metadata']['files_generated']}")
                print(f"         Lines of code: {implementation['metadata']['total_lines_of_code']}")
                if pr_url:
                    print(f"         PR URL: {pr_url}")
                implementations_generated += 1

        finally:
            producer.flush()

    print("\n" + "="*80)
    print(f"✅ IMPLEMENTATION AGENT COMPLETE")
    print(f"   Implementations generated: {implementations_generated}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Implementation Agent - Generate implementation artifacts")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read from files instead of Kafka (for testing)"
    )
    parser.add_argument(
        "--no-claude",
        action="store_true",
        help="Use fallback logic instead of Claude API"
    )
    parser.add_argument(
        "--limit-one",
        action="store_true",
        help="Process only one approved solution (useful for testing)"
    )

    args = parser.parse_args()

    try:
        run_agent(dry_run=args.dry_run, use_claude=not args.no_claude, limit_one=args.limit_one)
    except KeyboardInterrupt:
        print("\n\n⚠️  Agent interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Agent failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
