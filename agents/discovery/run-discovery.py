#!/usr/bin/env python3
"""
Discovery Agent using Confluent MCP
Inventories all topics, schemas, and connectors
"""

import asyncio
import json
from datetime import datetime, UTC
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_mcp_command(session, tool_name, parameters=None):
    """Execute MCP tool via Confluent MCP server"""
    # Call the tool with parameters
    result = await session.call_tool(tool_name, arguments=parameters or {})

    # Extract the content from the result
    if result.content:
        # MCP tools return TextContent or ImageContent
        # For Confluent tools, we expect TextContent with JSON
        for content in result.content:
            if hasattr(content, 'text'):
                try:
                    parsed = json.loads(content.text)
                    return parsed
                except json.JSONDecodeError:
                    # Return raw text if not JSON
                    return content.text

    return None

async def discover_topics(session):
    """Discover all Kafka topics"""
    print("Discovering topics...")
    topics_response = await run_mcp_command(session, "list-topics")

    # Parse the response - it's plain text like "Kafka topics: topic1,topic2,topic3"
    topics = []
    if isinstance(topics_response, str):
        if "Kafka topics:" in topics_response:
            topics_str = topics_response.split("Kafka topics:")[1].strip()
            topics = [t.strip() for t in topics_str.split(",") if t.strip()]

    print(f"Found {len(topics)} topics")

    # For now, just return the topic names
    # TODO: Add topic config retrieval once we determine the correct tool name
    topic_details = [{"name": topic} for topic in topics]

    return topic_details

async def discover_schemas(session):
    """Discover all Schema Registry schemas"""
    print("Discovering schemas...")
    schemas_response = await run_mcp_command(session, "list-schemas")

    # Parse the response - it's a JSON dict with subject names as keys
    schema_details = []
    if isinstance(schemas_response, dict):
        print(f"Found {len(schemas_response)} schema subjects")
        for subject, versions in schemas_response.items():
            print(f"  - Schema subject: {subject}")
            schema_details.append({
                "subject": subject,
                "versions": versions
            })

    return schema_details

async def discover_connectors(session):
    """Discover all connectors"""
    print("Discovering connectors...")
    connectors_response = await run_mcp_command(session, "list-connectors")

    # Parse the response - it might be JSON or plain text
    connector_details = []
    if isinstance(connectors_response, dict):
        # If it's a dict, the connector names might be in the keys or values
        print(f"Found {len(connectors_response)} connectors (dict response)")
        for name, info in connectors_response.items():
            connector_details.append({
                "name": name,
                "info": info
            })
    elif isinstance(connectors_response, list):
        # If it's a list of connector names
        print(f"Found {len(connectors_response)} connectors")
        for connector in connectors_response:
            connector_details.append({"name": connector})
    elif isinstance(connectors_response, str):
        # Parse plain text like "Active Connectors: connector1,connector2,connector3"
        if "Active Connectors:" in connectors_response:
            connectors_str = connectors_response.split("Active Connectors:")[1].strip()
            # Remove quotes if present
            connectors_str = connectors_str.strip('"')
            connectors = [c.strip() for c in connectors_str.split(",") if c.strip()]
            print(f"Found {len(connectors)} connectors")
            for connector in connectors:
                connector_details.append({"name": connector})

    return connector_details

async def main():
    """Run full discovery"""
    output_dir = Path("./discovery-outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(UTC).isoformat()

    # Configure connection to Confluent MCP server via npx
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@confluentinc/mcp-confluent", "-e", ".env"],
        env=None
    )

    # Use proper async context managers
    print("Connecting to Confluent MCP server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected!")

            # Run discovery
            topics = await discover_topics(session)
            schemas = await discover_schemas(session)
            connectors = await discover_connectors(session)

            inventory = {
                "environment": "agentic-data-mesh",
                "cluster": "data-mesh-cluster",
                "discovery_timestamp": timestamp,
                "topics": topics,
                "schemas": schemas,
                "connectors": connectors
            }

            # Save inventory
            output_file = output_dir / f"inventory-{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(inventory, f, indent=2)

            print(f"\nDiscovery complete! Inventory saved to {output_file}")
            print(f"Found {len(inventory['topics'])} topics")
            print(f"Found {len(inventory['schemas'])} schemas")
            print(f"Found {len(inventory['connectors'])} connectors")

if __name__ == "__main__":
    asyncio.run(main())