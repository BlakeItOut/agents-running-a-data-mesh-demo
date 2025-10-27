#!/usr/bin/env python3
"""
Deployment Agent

Analyzes raw Confluent Cloud state (topics, schemas, connectors) and publishes
to the agent-state-deployment topic.

Uses Confluent MCP for discovery (similar to Discovery Agent prototype).
"""

import asyncio
import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
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


async def run_deployment_agent():
    """Main deployment agent logic"""
    print("=" * 60)
    print("DEPLOYMENT AGENT")
    print("=" * 60)

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

            # Publish to Kafka
            print("\n4. Publishing to agent-state-deployment topic...")
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

                print("   ✅ Deployment state published successfully!")

            except Exception as e:
                print(f"   ❌ Failed to publish: {e}")
                raise

    print("\n" + "=" * 60)
    print("DEPLOYMENT AGENT COMPLETE")
    print("=" * 60)

    return deployment_state


if __name__ == "__main__":
    result = asyncio.run(run_deployment_agent())

    # Print summary
    print(f"\nSummary:")
    print(f"  Topics: {len(result['topics'])}")
    print(f"  Schemas: {len(result['schemas'])}")
    print(f"  Connectors: {len(result['connectors'])}")
    print(f"  Domains: {len(result['domains'])}")
