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


def load_approved_solutions_from_kafka():
    """Load all approved solutions from Kafka."""
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
    finally:
        consumer.close()

    return approved_solutions


def generate_implementation(solution, use_claude=True):
    """
    Use Claude to generate implementation artifacts for the solution.

    Args:
        solution: The approved solution design
        use_claude: Whether to use Claude API (False for fallback)

    Returns:
        dict: Implementation with generated artifacts
    """
    print(f"\n   Generating implementation for: {solution.get('idea_title')}")

    start_time = time.time()

    if not use_claude:
        return create_fallback_implementation(solution, start_time)

    # Prepare context
    idea_title = solution.get("idea_title", "Unknown")
    technical_approach = solution.get("technical_approach", "")
    processing_engine = solution.get("processing_engine", "KSQLDB")
    new_topics = solution.get("new_topics", [])
    schemas = solution.get("schemas", [])
    query_specs = solution.get("query_specifications", [])
    infrastructure = solution.get("infrastructure_requirements", {})
    governance = solution.get("data_governance", {})

    system_prompt = """You are an expert infrastructure-as-code engineer specializing in Confluent Cloud and Terraform.

Your role:
- Generate production-ready Terraform code for Confluent Cloud
- Create valid ksqlDB or Flink SQL queries
- Write clear documentation
- Follow Terraform best practices
- Ensure code is idempotent and safe

Terraform guidelines:
- Use `confluent_kafka_topic` for topics
- Use `confluent_schema` for schema registry
- Reference existing cluster and environment resources
- Include proper depends_on relationships
- Add meaningful comments

Query guidelines:
- Valid ksqlDB or Flink SQL syntax
- Include proper error handling
- Consider performance (indexing, partitioning)
- Add comments explaining logic

Documentation guidelines:
- Clear README with usage examples
- API documentation if applicable
- Deployment instructions
- Troubleshooting guide

Be thorough and production-ready."""

    prompt = f"""Generate complete implementation artifacts for this approved solution:

━━━ SOLUTION DESIGN ━━━
Title: {idea_title}
Technical Approach: {technical_approach}
Processing Engine: {processing_engine}

New Topics ({len(new_topics)}):
{json.dumps(new_topics, indent=2)}

Schemas ({len(schemas)}):
{json.dumps(schemas, indent=2)}

Query Specifications ({len(query_specs)}):
{json.dumps(query_specs, indent=2)}

Infrastructure Requirements:
{json.dumps(infrastructure, indent=2)}

Data Governance:
{json.dumps(governance, indent=2)}

━━━ YOUR TASK ━━━
Generate complete implementation artifacts:

1. **Terraform Code** (terraform/data-products/<product-name>.tf)
   - Create topics with proper configuration
   - Register schemas with Schema Registry
   - Reference existing cluster: confluent_kafka_cluster.datagen_cluster
   - Reference existing environment: confluent_environment.datagen_env
   - Use existing admin API key: confluent_api_key.cluster_admin_api_key
   - Include resource dependencies

2. **ksqlDB/Flink SQL Queries** (if applicable)
   - Full query definitions
   - Proper syntax for chosen engine
   - Comments explaining logic

3. **README Documentation**
   - Overview of the data product
   - Usage examples
   - Query patterns
   - API documentation (if applicable)

4. **Deployment Plan**
   - Step-by-step deployment instructions
   - Validation steps
   - Rollback procedure

5. **Test Plan**
   - Unit tests for queries
   - Integration tests
   - Validation tests

6. **Cost Estimation**
   - Break down monthly costs
   - Consider storage, compute, throughput

7. **Pull Request Information**
   - Branch name (feat/data-product-<name>)
   - PR title
   - PR description with context

IMPORTANT: You must respond with ONLY a valid JSON object. Do not include markdown headers, explanations, or code fences. Start your response with {{ and end with }}. Output only the JSON structure below:
{{
  "artifacts": [
    {{
      "path": "terraform/data-products/gaming-analytics.tf",
      "type": "TERRAFORM",
      "content": "# Gaming Analytics Data Product\\n\\nresource \\"confluent_kafka_topic\\" \\"gaming_analytics\\" {{\\n  kafka_cluster {{\\n    id = confluent_kafka_cluster.datagen_cluster.id\\n  }}\\n  ...\\n}}",
      "description": "Terraform configuration for gaming analytics topics and schemas"
    }},
    {{
      "path": "queries/gaming-analytics.sql",
      "type": "KSQLDB",
      "content": "-- Gaming Analytics ksqlDB Queries\\n\\nCREATE STREAM ...",
      "description": "ksqlDB queries for gaming analytics"
    }},
    {{
      "path": "docs/data-products/gaming-analytics-README.md",
      "type": "DOCUMENTATION",
      "content": "# Gaming Analytics Data Product\\n\\n## Overview\\n...",
      "description": "Documentation for gaming analytics data product"
    }}
  ],
  "terraform_resources": [
    {{
      "resource_type": "confluent_kafka_topic",
      "resource_name": "gaming_analytics_sessions",
      "description": "Topic for gaming session data"
    }},
    {{
      "resource_type": "confluent_schema",
      "resource_name": "gaming_analytics_sessions_schema",
      "description": "Avro schema for session events"
    }}
  ],
  "pull_request": {{
    "branch_name": "feat/data-product-gaming-analytics",
    "title": "Add Gaming Analytics Data Product",
    "description": "## Summary\\n\\nImplements the Gaming Analytics data product as designed by the Solution Agent.\\n\\n## What's Included\\n\\n- Kafka topics for analytics\\n- Avro schemas\\n- ksqlDB queries for sessionization\\n\\n## Deployment\\n\\nSee docs/data-products/gaming-analytics-README.md for deployment instructions.\\n\\n## Testing\\n\\nValidation tests included in test plan.",
    "base_branch": "main",
    "labels": ["agent-generated", "data-product", "{governance.get('domain', 'unknown')}"],
    "url": null
  }},
  "deployment_plan": {{
    "steps": [
      {{
        "order": 1,
        "description": "Review and merge PR",
        "command": "gh pr merge <pr-number> --auto",
        "estimated_duration": "5 minutes"
      }},
      {{
        "order": 2,
        "description": "Apply Terraform changes",
        "command": "cd terraform && terraform apply",
        "estimated_duration": "10-15 minutes"
      }},
      {{
        "order": 3,
        "description": "Deploy ksqlDB queries",
        "command": "ksql < queries/gaming-analytics.sql",
        "estimated_duration": "5 minutes"
      }},
      {{
        "order": 4,
        "description": "Validate data product",
        "command": "Run validation tests",
        "estimated_duration": "10 minutes"
      }}
    ],
    "rollback_procedure": "If deployment fails: 1) Stop ksqlDB queries, 2) terraform destroy for new resources, 3) revert PR",
    "validation_steps": [
      "Verify topics exist in Confluent Cloud UI",
      "Verify schemas registered in Schema Registry",
      "Query ksqlDB to confirm data flowing",
      "Check monitoring dashboards for errors"
    ]
  }},
  "documentation": {{
    "readme_content": "# Gaming Analytics Data Product\\n\\nFull README content...",
    "usage_examples": [
      "-- Query active gaming sessions\\nSELECT * FROM gaming_sessions WHERE status = 'active';",
      "-- Get player statistics\\nSELECT player_id, COUNT(*) as session_count FROM gaming_sessions GROUP BY player_id;"
    ],
    "api_documentation": "GET /api/v1/gaming/sessions - Returns active gaming sessions\\nQuery params: player_id, start_time, end_time"
  }},
  "estimated_cost": {{
    "monthly_usd": 150.0,
    "breakdown": [
      {{
        "component": "Kafka topics (3 topics, 6 partitions each)",
        "monthly_usd": 50.0
      }},
      {{
        "component": "ksqlDB cluster (4 CSUs)",
        "monthly_usd": 100.0
      }}
    ]
  }},
  "test_plan": [
    {{
      "name": "Schema validation",
      "description": "Verify all Avro schemas are valid and registered",
      "test_type": "VALIDATION"
    }},
    {{
      "name": "Query correctness",
      "description": "Test ksqlDB queries produce expected results",
      "test_type": "INTEGRATION"
    }},
    {{
      "name": "End-to-end data flow",
      "description": "Verify data flows from source to data product",
      "test_type": "E2E"
    }}
  ],
  "metadata": {{
    "agent_version": "1.0.0",
    "generation_time_seconds": 15.0,
    "files_generated": 3,
    "total_lines_of_code": 250
  }},
  "confidence_score": 0.85
}}

Generate realistic, production-ready code. Use actual Terraform syntax and valid SQL."""

    response = call_claude(system_prompt, prompt)

    try:
        # Parse JSON from Claude's response
        response_text = response.strip()

        # Try to extract JSON from markdown code blocks
        if "```json" in response_text:
            # Extract content between ```json and ```
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            if json_end != -1:
                response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            # Extract content between ``` markers
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            if json_end != -1:
                response_text = response_text[json_start:json_end].strip()

        # If response starts with markdown headers, find the JSON object
        if not response_text.startswith("{"):
            # Find the first { which should be the JSON start
            json_start_idx = response_text.find("{")
            if json_start_idx != -1:
                response_text = response_text[json_start_idx:]

        # Find the last } to handle any trailing content
        if not response_text.endswith("}"):
            json_end_idx = response_text.rfind("}")
            if json_end_idx != -1:
                response_text = response_text[:json_end_idx + 1]

        analysis = json.loads(response_text)

        generation_time = time.time() - start_time

        # Count files and lines
        artifacts = analysis.get("artifacts", [])
        total_lines = sum(len(a.get("content", "").split('\n')) for a in artifacts)

        # Build implementation message
        implementation = {
            "timestamp": datetime.now(UTC).isoformat(),
            "implementation_id": str(uuid.uuid4()),
            "solution_id": solution.get("solution_id"),
            "idea_id": solution.get("idea_id"),
            "idea_title": solution.get("idea_title"),
            "artifacts": artifacts,
            "terraform_resources": analysis.get("terraform_resources", []),
            "pull_request": analysis.get("pull_request", {}),
            "deployment_plan": analysis.get("deployment_plan", {}),
            "documentation": analysis.get("documentation", {}),
            "estimated_cost": analysis.get("estimated_cost", {}),
            "test_plan": analysis.get("test_plan", []),
            "metadata": {
                "agent_version": "1.0.0",
                "generation_time_seconds": generation_time,
                "files_generated": len(artifacts),
                "total_lines_of_code": total_lines
            },
            "confidence_score": analysis.get("confidence_score", 0.7),
            "status": "GENERATED"
        }

        return implementation

    except json.JSONDecodeError as e:
        print(f"      ⚠️  Failed to parse Claude response as JSON: {e}")
        print(f"      Raw response: {response[:200]}...")
        return create_fallback_implementation(solution, start_time)
    except Exception as e:
        print(f"      ⚠️  Error in generate_implementation: {e}")
        import traceback
        traceback.print_exc()
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
            "labels": ["agent-generated", "data-product"],
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
        for artifact in implementation.get("artifacts", []):
            file_path = artifact["path"]
            subprocess.run(
                ["git", "add", file_path],
                cwd=repo_root,
                check=True,
                capture_output=True
            )

        # Commit
        commit_message = f"{pr_title}\n\n{pr_description}\n\nGenerated by Implementation Agent"
        print(f"      Committing changes...")
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_root,
            check=True,
            capture_output=True
        )

        # Push to remote
        print(f"      Pushing to remote...")
        subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=repo_root,
            check=True,
            capture_output=True
        )

        # Create PR using gh CLI
        print(f"      Creating PR with gh CLI...")
        gh_command = [
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", pr_description,
            "--base", base_branch
        ]

        # Add labels if provided
        for label in labels:
            gh_command.extend(["--label", label])

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
        if e.stderr:
            print(f"         Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")

        # Try to return to original branch if we changed it
        try:
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
        approved_solutions = load_approved_solutions_from_kafka()

        # Limit to one if requested
        if limit_one and len(approved_solutions) > 1:
            approved_solutions = [approved_solutions[0]]

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

    args = parser.parse_args()

    try:
        run_agent(dry_run=args.dry_run, use_claude=not args.no_claude)
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
