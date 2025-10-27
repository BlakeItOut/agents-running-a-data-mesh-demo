#!/usr/bin/env python3
"""
Deployment Agent

Analyzes raw Confluent Cloud state (topics, schemas, connectors) and publishes
to the agent-state-deployment topic.

Uses Confluent MCP for discovery (similar to Discovery Agent prototype).
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# MCP imports are only needed for non-dry-run mode
# Import them conditionally to avoid dependency issues in dry-run
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from common.kafka_utils import create_avro_producer, produce_message
from common.schema_utils import get_schema_string


async def run_mcp_command(session, tool_name, parameters=None):
    """Execute MCP tool via Confluent MCP server"""
    result = await session.call_tool(tool_name, arguments=parameters or {})

    if result.content:
        for content in result.content:
            if hasattr(content, 'text'):
                try:
                    parsed = json.loads(content.text)
                    return parsed
                except json.JSONDecodeError:
                    return content.text

    return None


async def discover_topics(session):
    """Discover all Kafka topics"""
    print("  Discovering topics...")
    topics_response = await run_mcp_command(session, "list-topics")

    topics = []
    if isinstance(topics_response, str):
        if "Kafka topics:" in topics_response:
            topics_str = topics_response.split("Kafka topics:")[1].strip()
            topic_names = [t.strip() for t in topics_str.split(",") if t.strip()]
            topics = [{"name": name, "partitions": None, "replication_factor": None}
                     for name in topic_names]

    print(f"  Found {len(topics)} topics")
    return topics


async def discover_schemas(session):
    """Discover all Schema Registry schemas"""
    print("  Discovering schemas...")
    schemas_response = await run_mcp_command(session, "list-schemas")

    schema_details = []
    if isinstance(schemas_response, dict):
        for subject, versions in schemas_response.items():
            if versions and len(versions) > 0:
                latest_version = versions[0]  # First version is latest

                # Extract namespace from schema if available
                namespace = None
                if 'schema' in latest_version:
                    try:
                        schema_obj = json.loads(latest_version['schema'])
                        namespace = schema_obj.get('namespace')
                    except:
                        pass

                schema_details.append({
                    "subject": subject,
                    "version": latest_version.get('version', 1),
                    "schema_id": latest_version.get('id', 0),
                    "schema_type": "AVRO",
                    "namespace": namespace
                })

    print(f"  Found {len(schema_details)} schemas")
    return schema_details


async def discover_connectors(session):
    """Discover all connectors"""
    print("  Discovering connectors...")
    connectors_response = await run_mcp_command(session, "list-connectors")

    connector_details = []
    if isinstance(connectors_response, str):
        if "Active Connectors:" in connectors_response:
            connectors_str = connectors_response.split("Active Connectors:")[1].strip().strip('"')
            connector_names = [c.strip() for c in connectors_str.split(",") if c.strip()]
            connector_details = [
                {"name": name, "type": "source", "status": "RUNNING"}
                for name in connector_names
            ]

    print(f"  Found {len(connector_details)} connectors")
    return connector_details


def analyze_domains(schemas):
    """Group topics by domain based on schema namespaces"""
    domains = defaultdict(lambda: {"topics": [], "topic_count": 0})

    for schema in schemas:
        namespace = schema.get('namespace')
        if not namespace:
            namespace = "unknown"

        # Extract domain from namespace (first part)
        domain = namespace.split('.')[0] if '.' in namespace else namespace

        # Extract topic name from subject (remove -value or -key suffix)
        subject = schema['subject']
        topic_name = subject.replace('-value', '').replace('-key', '')

        if topic_name not in domains[domain]["topics"]:
            domains[domain]["topics"].append(topic_name)
            domains[domain]["topic_count"] = len(domains[domain]["topics"])

    return dict(domains)


def generate_synthetic_deployment_state():
    """
    Generate synthetic deployment state for dry-run mode.
    Based on actual Discovery Agent findings (37 topics, 12 domains).
    """
    timestamp = datetime.now(UTC).isoformat()

    # Synthetic topic data (from Discovery Agent prototype)
    all_topics = [
        "clickstream", "clickstream_codes", "clickstream_users",
        "gaming_games", "gaming_player_activity", "gaming_players",
        "pizza_orders", "pizza_orders_cancelled", "pizza_orders_completed",
        "campaign_finance", "credit_cards", "purchases", "stores", "transactions",
        "device_information",
        "inventory", "orders", "pageviews", "product", "ratings", "stock_trades", "users",
        "fleet_mgmt_description", "fleet_mgmt_location", "fleet_mgmt_sensors",
        "payroll_bonus", "payroll_employee", "payroll_employee_location",
        "shoe_clickstream", "shoe_customers", "shoe_orders", "shoes",
        "siem_logs", "syslog_logs",
        "insurance_customer_activity", "insurance_customers", "insurance_offers"
    ]

    topics = [{"name": topic, "partitions": 6, "replication_factor": 3} for topic in all_topics]

    # Synthetic schema data with appropriate namespaces
    schemas = []
    schema_mapping = {
        "clickstream": ["clickstream", "clickstream_codes", "clickstream_users"],
        "gaming": ["gaming_games", "gaming_player_activity", "gaming_players"],
        "pizza_orders": ["pizza_orders", "pizza_orders_cancelled", "pizza_orders_completed"],
        "datagen": ["campaign_finance", "credit_cards", "purchases", "stores", "transactions"],
        "device_information": ["device_information"],
        "ksql": ["inventory", "orders", "pageviews", "product", "ratings", "stock_trades", "users"],
        "fleet_mgmt": ["fleet_mgmt_description", "fleet_mgmt_location", "fleet_mgmt_sensors"],
        "payroll": ["payroll_bonus", "payroll_employee", "payroll_employee_location"],
        "shoes": ["shoe_clickstream", "shoe_customers", "shoe_orders", "shoes"],
        "siem_logs": ["siem_logs"],
        "syslogs": ["syslog_logs"],
        "insurance": ["insurance_customer_activity", "insurance_customers", "insurance_offers"]
    }

    schema_id = 100001
    for namespace, topic_list in schema_mapping.items():
        for topic in topic_list:
            schemas.append({
                "subject": f"{topic}-value",
                "version": 1,
                "schema_id": schema_id,
                "schema_type": "AVRO",
                "namespace": namespace
            })
            schema_id += 1

    # Synthetic connector data
    connectors = [{"name": f"datagen-{topic}", "type": "source", "status": "RUNNING"}
                  for topic in all_topics]

    # Analyze domains from schemas
    domains = analyze_domains(schemas)

    deployment_state = {
        "timestamp": timestamp,
        "cluster_id": "lkc-synthetic",
        "environment_id": "env-synthetic",
        "topics": topics,
        "schemas": schemas,
        "connectors": connectors,
        "domains": domains
    }

    return deployment_state


async def run_deployment_agent(dry_run=False):
    """Main deployment agent logic"""
    print("=" * 60)
    print("DEPLOYMENT AGENT" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    if dry_run:
        # Dry run mode: Use synthetic data, skip MCP entirely
        print("\n1. Generating synthetic deployment state...")
        print("   Using data based on Discovery Agent prototype findings")
        print("   (37 topics across 12 domains)")

        deployment_state = generate_synthetic_deployment_state()

        print(f"   ✅ Generated synthetic data:")
        print(f"      Topics: {len(deployment_state['topics'])}")
        print(f"      Schemas: {len(deployment_state['schemas'])}")
        print(f"      Connectors: {len(deployment_state['connectors'])}")
        print(f"      Domains: {len(deployment_state['domains'])}")

    else:
        # Normal mode: Connect to MCP and discover real data
        if not MCP_AVAILABLE:
            print("❌ MCP library not available. Install with: pip install mcp")
            print("   Or run in dry-run mode: python deployment.py --dry-run")
            raise ImportError("MCP library required for normal mode")

        timestamp = datetime.now(UTC).isoformat()

        # Configure connection to Confluent MCP server
        print("\n1. Connecting to Confluent MCP server...")

        # Check for .env file in agents/discovery directory (from prototype)
        discovery_env_path = Path(__file__).parent.parent / "discovery" / ".env"
        env_arg = str(discovery_env_path) if discovery_env_path.exists() else ".env"

        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@confluentinc/mcp-confluent", "-e", env_arg],
            env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("   Connected!")

                # Run discovery
                print("\n2. Running discovery...")
                topics = await discover_topics(session)
                schemas = await discover_schemas(session)
                connectors = await discover_connectors(session)

                # Analyze domains
                print("\n3. Analyzing domains...")
                domains = analyze_domains(schemas)
                print(f"   Found {len(domains)} domains")

                # Build deployment state
                deployment_state = {
                    "timestamp": timestamp,
                    "cluster_id": "lkc-nd1ng3",  # TODO: Get from environment
                    "environment_id": "env-7zpqx1",  # TODO: Get from environment
                    "topics": topics,
                    "schemas": schemas,
                    "connectors": connectors,
                    "domains": domains
                }

    # Publish to Kafka or save to file (applies to both dry-run and normal mode)
    print("\n2. Publishing deployment state..." if dry_run else "\n4. Publishing deployment state...")
    if dry_run:
        # Dry run: save to file
        output_dir = Path(__file__).parent.parent / "dry-run-output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "deployment-state.json"

        with open(output_file, 'w') as f:
            json.dump(deployment_state, f, indent=2)

        print(f"   💾 Dry run: Saved to {output_file}")
        print(f"   📊 Summary: {len(deployment_state['topics'])} topics, "
              f"{len(deployment_state['schemas'])} schemas, "
              f"{len(deployment_state['domains'])} domains")
    else:
        # Normal mode: publish to Kafka
        try:
            schema_str = get_schema_string("deployment-state")
            producer, serializer = create_avro_producer(schema_str)

            produce_message(
                producer=producer,
                serializer=serializer,
                topic="agent-state-deployment",
                key="data-mesh-cluster",
                value=deployment_state
            )

            print("   ✅ Deployment state published to Kafka successfully!")

        except Exception as e:
            print(f"   ❌ Failed to publish: {e}")
            raise

    print("\n" + "=" * 60)
    print("DEPLOYMENT AGENT COMPLETE")
    print("=" * 60)

    return deployment_state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deployment Agent - Discovers Confluent Cloud state")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run mode: save output to file instead of publishing to Kafka")
    args = parser.parse_args()

    result = asyncio.run(run_deployment_agent(dry_run=args.dry_run))

    # Print summary
    print(f"\nSummary:")
    print(f"  Topics: {len(result['topics'])}")
    print(f"  Schemas: {len(result['schemas'])}")
    print(f"  Connectors: {len(result['connectors'])}")
    print(f"  Domains: {len(result['domains'])}")
