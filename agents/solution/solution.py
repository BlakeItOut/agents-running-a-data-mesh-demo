#!/usr/bin/env python3
"""
Solution Agent - Solution Layer (Phase 4)

Designs technical solutions for approved data product ideas.
Takes approved decisions and creates detailed technical specifications including:
- Processing engine selection (ksqlDB, Flink, Kafka Streams, etc.)
- New topic definitions
- Avro schema specifications
- Query/transformation logic
- Infrastructure requirements
- Data governance policies

Consumes approved decisions and produces solution designs.
"""

import argparse
import json
import sys
import uuid
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
from common.claude_utils import call_claude


def load_decision_from_file(idea_id):
    """Load approved decision for a specific idea from dry-run output files."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"

    for decision_file in output_dir.glob("decision-*.json"):
        with open(decision_file, 'r') as f:
            decision = json.load(f)
            if decision.get("idea_id") == idea_id and decision.get("status") == "APPROVED":
                return decision

    return None


def load_idea_from_file(idea_id):
    """Load the original idea from dry-run output files."""
    output_dir = Path(__file__).parent.parent / "dry-run-output"

    for idea_file in output_dir.glob("raw-idea-*.json"):
        with open(idea_file, 'r') as f:
            idea = json.load(f)
            if idea.get("idea_id") == idea_id:
                return idea

    return None


def load_approved_decisions_from_kafka(consume_one_only=False):
    """Load approved decisions from Kafka.

    Args:
        consume_one_only: If True, only consume one message (for demos)
    """
    print("   Loading approved decisions from Kafka...")

    approved_decisions = []

    schema_str = get_schema_string("decision")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"solution-agent-{datetime.now().timestamp()}"
    )
    consumer.subscribe(["agent-state-decisions"])

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
                approved_decisions.append(value)
                if consume_one_only:
                    break
    finally:
        consumer.close()

    return approved_decisions


def load_idea_from_kafka(idea_id):
    """Load the original idea from Kafka."""
    schema_str = get_schema_string("raw-ideas")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"solution-agent-idea-{datetime.now().timestamp()}"
    )
    consumer.subscribe(["agent-state-raw-ideas"])

    try:
        timeout_ms = 5000
        while True:
            msg = consumer.poll(timeout=timeout_ms / 1000.0)
            if msg is None:
                break
            if msg.error():
                continue

            value = deserializer(msg.value(), None)
            if value and value.get("idea_id") == idea_id:
                consumer.close()
                return value
    finally:
        consumer.close()

    return None


def load_current_state_from_kafka():
    """Load the current infrastructure state from Kafka for context."""
    schema_str = get_schema_string("current-state")
    consumer, deserializer = create_avro_consumer(
        schema_str,
        group_id=f"solution-agent-state-{datetime.now().timestamp()}"
    )
    message = consume_latest_message(
        consumer,
        deserializer,
        "agent-state-current",
        timeout=5.0
    )
    return message if message else None


def design_solution(idea, decision, current_state, use_claude=True):
    """
    Use Claude to design a technical solution for the approved idea.

    Args:
        idea: The original data product idea
        decision: The approved decision with evaluation details
        current_state: Current infrastructure state for context
        use_claude: Whether to use Claude API (False for fallback)

    Returns:
        dict: Solution design
    """
    print(f"\n   Designing solution for: {idea.get('title')}")

    if not use_claude:
        return create_fallback_solution(idea, decision)

    # Prepare context
    idea_title = idea.get("title", "Unknown")
    idea_description = idea.get("description", "")
    related_topics = idea.get("related_topics", [])
    domain = idea.get("domain", "unknown")
    estimated_complexity = idea.get("estimated_complexity", "MEDIUM")

    # Get evaluation insights
    key_findings = decision.get("key_findings", [])
    conditions = decision.get("conditions", [])
    overall_risk = decision.get("overall_risk", "MODERATE")

    # Get infrastructure context
    available_topics = []
    if current_state:
        deployment_summary = current_state.get("deployment_summary", "")
        available_topics = current_state.get("topics", [])[:10]  # Sample for context

    system_prompt = """You are an expert data platform architect designing technical solutions for data products on Confluent Cloud.

Your role:
- Design practical, production-ready solutions
- Choose appropriate processing engines (ksqlDB, Flink, Kafka Streams, connectors)
- Define topic schemas and data models
- Specify stream processing logic
- Consider cost, performance, and operational complexity

Choose processing engines wisely:
- **ksqlDB**: Simple SQL transformations, aggregations, joins (most common choice)
- **Flink**: Complex event processing, windowing, stateful computations, ML inference
- **Kafka Streams**: Custom Java/Scala apps with fine-grained control
- **Connectors**: Data movement to/from external systems
- **Mixed**: Combination of the above

Be practical:
- Start simple, use ksqlDB unless there's a compelling reason for Flink
- Minimize infrastructure (fewer compute pools = lower cost)
- Design for observability and debugging
- Consider schema evolution and backwards compatibility

Output comprehensive specifications ready for implementation."""

    prompt = f"""Design a technical solution for this approved data product:

━━━ DATA PRODUCT IDEA ━━━
Title: {idea_title}
Description: {idea_description}
Domain: {domain}
Complexity: {estimated_complexity}
Source Topics: {json.dumps(related_topics, indent=2)}

━━━ EVALUATION RESULTS ━━━
Overall Risk: {overall_risk}
Key Findings:
{json.dumps(key_findings, indent=2)}

Conditions for Approval:
{json.dumps(conditions if conditions else ["None specified"], indent=2)}

━━━ AVAILABLE INFRASTRUCTURE ━━━
Sample of existing topics (first 10):
{json.dumps(available_topics, indent=2)}

━━━ YOUR TASK ━━━
Design a complete technical solution including:

1. **Processing Engine Selection**
   - Choose: KAFKA_STREAMS, KSQLDB, FLINK, SPARK, CONNECTOR_ONLY, or MIXED
   - Explain your rationale

2. **New Topics** (if needed)
   - Topic names following conventions (e.g., "{domain}.product-name.event-type")
   - Partition count (consider throughput, key distribution)
   - Retention policy

3. **Avro Schemas**
   - Define schemas for new topics
   - Consider schema evolution
   - Include documentation fields

4. **Query Specifications**
   - SQL queries (ksqlDB or Flink SQL)
   - Transformation logic
   - Join/aggregation strategies

5. **Infrastructure Requirements**
   - Compute pools needed?
   - ksqlDB cluster needed?
   - Connectors needed?
   - Estimated CSU hours/month

6. **Data Governance**
   - Data classification (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)
   - Ownership
   - Tags for discovery

7. **Testing Strategy**
   - How to validate correctness
   - Performance testing approach

8. **Deployment Considerations**
   - Dependencies
   - Rollback plan
   - Migration strategy (if applicable)

9. **Risks & Mitigations**
   - Technical risks
   - How to mitigate them
   - Severity levels

10. **Success Metrics**
    - How to measure if this data product is successful

IMPORTANT: You must respond with ONLY a valid JSON object. Do not include markdown headers, explanations, or code fences. Start your response with {{ and end with }}. Output only the JSON structure below:
{{
  "technical_approach": "High-level overview...",
  "processing_engine": "KSQLDB",
  "processing_rationale": "Why this engine...",
  "new_topics": [
    {{
      "name": "{domain}.analytics.user-sessions",
      "partitions": 6,
      "retention_ms": 604800000,
      "description": "Sessionized user activity..."
    }}
  ],
  "schemas": [
    {{
      "subject": "{domain}.analytics.user-sessions-value",
      "schema_definition": "{{\\"type\\":\\"record\\",\\"name\\":\\"UserSession\\",\\"fields\\":[...]}}",
      "description": "User session schema"
    }}
  ],
  "query_specifications": [
    {{
      "name": "user_sessions_stream",
      "type": "STREAM",
      "sql_template": "CREATE STREAM user_sessions WITH (KAFKA_TOPIC='{domain}.analytics.user-sessions', VALUE_FORMAT='AVRO') AS SELECT ...",
      "description": "Sessionize clickstream data"
    }}
  ],
  "infrastructure_requirements": {{
    "compute_pool_required": false,
    "ksqldb_cluster_required": true,
    "connectors_required": [],
    "estimated_csu_hours": null,
    "additional_notes": "Use existing ksqlDB cluster if available"
  }},
  "data_governance": {{
    "owner": "data-mesh-team",
    "domain": "{domain}",
    "classification": "INTERNAL",
    "retention_policy": "7 days",
    "tags": ["analytics", "user-behavior", "session-data"]
  }},
  "api_specifications": [
    {{
      "endpoint_pattern": "/api/v1/{domain}/user-sessions",
      "method": "GET",
      "description": "Query user sessions by user_id or time range"
    }}
  ],
  "testing_strategy": "Detailed testing approach...",
  "deployment_considerations": "Step-by-step deployment...",
  "estimated_effort_hours": 40.0,
  "risks_and_mitigations": [
    {{
      "risk": "High cardinality keys causing skew",
      "mitigation": "Monitor partition distribution, use composite keys",
      "severity": "MEDIUM"
    }}
  ],
  "success_metrics": [
    "Query response time < 2 seconds",
    "Data freshness < 30 seconds",
    "Adoption by 3+ downstream applications within 2 months"
  ],
  "confidence_score": 0.85
}}

Be thorough and specific. This will be used for implementation."""

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

        # Build solution message
        solution = {
            "timestamp": datetime.now(UTC).isoformat(),
            "solution_id": str(uuid.uuid4()),
            "idea_id": idea.get("idea_id"),
            "idea_title": idea_title,
            "technical_approach": analysis.get("technical_approach", ""),
            "processing_engine": analysis.get("processing_engine", "KSQLDB"),
            "processing_rationale": analysis.get("processing_rationale", ""),
            "new_topics": analysis.get("new_topics", []),
            "schemas": analysis.get("schemas", []),
            "query_specifications": analysis.get("query_specifications", []),
            "infrastructure_requirements": analysis.get("infrastructure_requirements", {}),
            "data_governance": analysis.get("data_governance", {}),
            "api_specifications": analysis.get("api_specifications", []),
            "testing_strategy": analysis.get("testing_strategy", ""),
            "deployment_considerations": analysis.get("deployment_considerations", ""),
            "estimated_effort_hours": analysis.get("estimated_effort_hours", 40.0),
            "risks_and_mitigations": analysis.get("risks_and_mitigations", []),
            "success_metrics": analysis.get("success_metrics", []),
            "confidence_score": analysis.get("confidence_score", 0.7),
            "status": "PENDING_APPROVAL"
        }

        return solution

    except json.JSONDecodeError as e:
        print(f"      ⚠️  Failed to parse Claude response as JSON: {e}")
        print(f"      Raw response: {response[:200]}...")
        return create_fallback_solution(idea, decision)
    except Exception as e:
        print(f"      ⚠️  Error in design_solution: {e}")
        return create_fallback_solution(idea, decision)


def create_fallback_solution(idea, decision):
    """Create a basic solution when Claude is unavailable."""
    print("      Using fallback solution design...")

    idea_title = idea.get("title", "Unknown")
    domain = idea.get("domain", "unknown")
    related_topics = idea.get("related_topics", [])

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "solution_id": str(uuid.uuid4()),
        "idea_id": idea.get("idea_id"),
        "idea_title": idea_title,
        "technical_approach": f"Basic ksqlDB solution aggregating data from {len(related_topics)} source topics",
        "processing_engine": "KSQLDB",
        "processing_rationale": "ksqlDB chosen for simple SQL-based transformations and aggregations",
        "new_topics": [
            {
                "name": f"{domain}.{idea_title.lower().replace(' ', '-')}",
                "partitions": 6,
                "retention_ms": 604800000,
                "description": f"Aggregated data for {idea_title}"
            }
        ],
        "schemas": [],
        "query_specifications": [],
        "infrastructure_requirements": {
            "compute_pool_required": False,
            "ksqldb_cluster_required": True,
            "connectors_required": [],
            "estimated_csu_hours": None,
            "additional_notes": "Use existing ksqlDB cluster"
        },
        "data_governance": {
            "owner": "data-mesh-team",
            "domain": domain,
            "classification": "INTERNAL",
            "retention_policy": "7 days",
            "tags": [domain, "data-product"]
        },
        "api_specifications": [],
        "testing_strategy": "Manual validation of query results against source data",
        "deployment_considerations": "Deploy ksqlDB queries incrementally, monitor for errors",
        "estimated_effort_hours": 40.0,
        "risks_and_mitigations": [],
        "success_metrics": ["Data product successfully deployed and queryable"],
        "confidence_score": 0.5,
        "status": "PENDING_APPROVAL"
    }


def run_agent(dry_run=False, use_claude=True, limit_one=False):
    """
    Main agent logic.

    Args:
        dry_run: If True, read from files and write to files instead of Kafka
        use_claude: If True, use Claude API; otherwise use fallback logic
        limit_one: If True, only process one approved decision (for demo/interactive mode)
    """
    print("\n" + "="*80)
    print("SOLUTION AGENT - Phase 4")
    print("Designing technical solutions for approved data product ideas")
    print("="*80 + "\n")

    solutions_generated = 0

    if dry_run:
        print("📁 DRY RUN MODE: Reading from files, writing to files\n")

        # Find all approved decisions
        output_dir = Path(__file__).parent.parent / "dry-run-output"
        approved_decisions = []

        for decision_file in output_dir.glob("decision-*.json"):
            with open(decision_file, 'r') as f:
                decision = json.load(f)
                if decision.get("status") == "APPROVED":
                    approved_decisions.append(decision)

        # Limit to one if requested
        if limit_one and len(approved_decisions) > 1:
            approved_decisions = [approved_decisions[0]]

        print(f"   Found {len(approved_decisions)} approved decision(s)")

        for decision in approved_decisions:
            idea_id = decision.get("idea_id")
            idea = load_idea_from_file(idea_id)

            if not idea:
                print(f"      ⚠️  Could not find idea {idea_id}")
                continue

            # Design solution
            solution = design_solution(idea, decision, None, use_claude=use_claude)

            # Write to file
            output_file = output_dir / f"solution-{solution['solution_id']}.json"
            with open(output_file, 'w') as f:
                json.dump(solution, f, indent=2)

            print(f"      ✅ Solution generated: {output_file.name}")
            solutions_generated += 1

    else:
        print("☁️  KAFKA MODE: Reading from and writing to Kafka topics\n")

        # Load approved decisions from Kafka
        approved_decisions = load_approved_decisions_from_kafka(consume_one_only=limit_one)

        print(f"   Found {len(approved_decisions)} approved decision(s)")

        if len(approved_decisions) == 0:
            print("\n   No approved decisions to design solutions for.")
            return

        # Load current state for context
        current_state = load_current_state_from_kafka()

        # Set up producer
        schema_str = get_schema_string("solution")
        producer, serializer = create_avro_producer(schema_str)

        try:
            for decision in approved_decisions:
                idea_id = decision.get("idea_id")
                idea = load_idea_from_kafka(idea_id)

                if not idea:
                    print(f"      ⚠️  Could not find idea {idea_id}")
                    continue

                # Design solution
                solution = design_solution(idea, decision, current_state, use_claude=use_claude)

                # Publish to Kafka
                produce_message(
                    producer=producer,
                    serializer=serializer,
                    topic="agent-state-solutions",
                    key=solution["solution_id"],
                    value=solution
                )

                print(f"      ✅ Solution published to Kafka")
                solutions_generated += 1

        finally:
            producer.flush()

    print("\n" + "="*80)
    print(f"✅ SOLUTION AGENT COMPLETE")
    print(f"   Solutions generated: {solutions_generated}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Solution Agent - Design technical solutions")
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
