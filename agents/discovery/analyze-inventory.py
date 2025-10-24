#!/usr/bin/env python3
"""
Analyze discovered inventory and suggest data products
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, UTC


def parse_schema(schema_json_str):
    """Parse Avro schema JSON string"""
    try:
        return json.loads(schema_json_str)
    except:
        return None


def extract_domain_from_namespace(namespace):
    """Extract domain from schema namespace"""
    if not namespace:
        return "unknown"
    # Common patterns: clickstream, gaming, pizza_orders, etc.
    parts = namespace.split('.')
    return parts[0] if parts else "unknown"


def analyze_inventory(inventory_file):
    """Analyze inventory and suggest data products"""

    with open(inventory_file, 'r') as f:
        inventory = json.load(f)

    print("=" * 80)
    print("DATA MESH DISCOVERY ANALYSIS")
    print("=" * 80)
    print(f"Environment: {inventory['environment']}")
    print(f"Cluster: {inventory['cluster']}")
    print(f"Discovery Time: {inventory['discovery_timestamp']}")
    print(f"\nTotal Topics: {len(inventory['topics'])}")
    print(f"Total Schemas: {len(inventory['schemas'])}")
    print(f"Total Connectors: {len(inventory['connectors'])}")
    print()

    # Group topics by domain based on schema namespaces
    domains = defaultdict(lambda: {
        'topics': [],
        'schemas': [],
        'fields': set(),
        'entity_types': set()
    })

    # Parse schemas and group by domain
    for schema_info in inventory['schemas']:
        subject = schema_info['subject']
        topic_name = subject.replace('-value', '').replace('-key', '')

        for version in schema_info['versions']:
            schema = parse_schema(version['schema'])
            if schema:
                namespace = schema.get('namespace', 'unknown')
                domain = extract_domain_from_namespace(namespace)

                domains[domain]['topics'].append(topic_name)
                domains[domain]['schemas'].append(subject)

                # Extract field names to identify entity types
                if 'fields' in schema:
                    for field in schema['fields']:
                        domains[domain]['fields'].add(field['name'])

                # Record entity type
                if 'name' in schema:
                    domains[domain]['entity_types'].add(schema['name'])

    # Print domain analysis
    print("=" * 80)
    print("DISCOVERED DOMAINS")
    print("=" * 80)
    for domain, info in sorted(domains.items()):
        print(f"\n{domain.upper()} Domain:")
        print(f"  Topics: {len(set(info['topics']))}")
        print(f"  Unique topics: {', '.join(sorted(set(info['topics'])))}")

    # Suggest data products
    print("\n" + "=" * 80)
    print("SUGGESTED DATA PRODUCTS")
    print("=" * 80)

    suggestions = []

    for domain, info in sorted(domains.items()):
        if domain == 'unknown':
            continue

        unique_topics = set(info['topics'])
        if len(unique_topics) >= 2:  # Multi-topic domains are good data product candidates
            suggestions.append({
                'domain': domain,
                'name': f"{domain.replace('_', '-')}-data-product",
                'topics': sorted(unique_topics),
                'entity_types': sorted(info['entity_types']),
                'rationale': f"Related topics in {domain} domain with cohesive schema namespace"
            })

    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion['name'].upper()}")
        print(f"   Domain: {suggestion['domain']}")
        print(f"   Topics ({len(suggestion['topics'])}):")
        for topic in suggestion['topics']:
            print(f"     - {topic}")
        print(f"   Entity Types: {', '.join(suggestion['entity_types'])}")
        print(f"   Rationale: {suggestion['rationale']}")

    # Suggest improvements
    print("\n" + "=" * 80)
    print("RECOMMENDED IMPROVEMENTS")
    print("=" * 80)

    improvements = []

    # 1. Identify inconsistent naming
    topic_names = [t['name'] for t in inventory['topics']]
    naming_issues = []
    for topic in topic_names:
        if '_' in topic:  # Snake case
            if any('-' in t for t in topic_names):
                naming_issues.append(topic)

    if naming_issues:
        improvements.append({
            'type': 'Naming Consistency',
            'priority': 'Medium',
            'description': 'Standardize topic naming convention (snake_case vs kebab-case)',
            'affected_topics': naming_issues[:5],  # Show first 5
            'action': 'Choose one naming convention and apply consistently across all topics'
        })

    # 2. Identify domains with single topics (might need more context)
    for domain, info in domains.items():
        if domain != 'unknown' and len(set(info['topics'])) == 1:
            improvements.append({
                'type': 'Domain Isolation',
                'priority': 'Low',
                'description': f'{domain} domain has only one topic - consider if this should be part of a larger domain',
                'affected_topics': list(set(info['topics'])),
                'action': f'Review if {list(info["topics"])[0]} should be grouped with related domains'
            })

    # 3. Identify topics without clear domain (datagen.example namespace)
    datagen_topics = [t for t in domains.get('datagen', {}).get('topics', [])]
    if datagen_topics:
        improvements.append({
            'type': 'Schema Namespace Quality',
            'priority': 'High',
            'description': 'Topics using generic "datagen.example" namespace instead of domain-specific namespace',
            'affected_topics': sorted(set(datagen_topics)),
            'action': 'Update schema namespaces to reflect actual business domain'
        })

    # 4. Suggest adding business metadata
    improvements.append({
        'type': 'Metadata Enhancement',
        'priority': 'High',
        'description': 'Add business metadata to topics for better discoverability',
        'affected_topics': ['all topics'],
        'action': 'Add tags, descriptions, owner information, and SLAs using Stream Catalog'
    })

    # 5. Schema Evolution Strategy
    single_version_schemas = [s['subject'] for s in inventory['schemas'] if len(s['versions']) == 1]
    if len(single_version_schemas) == len(inventory['schemas']):
        improvements.append({
            'type': 'Schema Evolution',
            'priority': 'Medium',
            'description': 'All schemas are on version 1 - establish schema evolution strategy',
            'affected_topics': ['all schemas'],
            'action': 'Define schema compatibility rules and versioning strategy for future changes'
        })

    for i, improvement in enumerate(improvements, 1):
        print(f"\n{i}. [{improvement['priority']}] {improvement['type']}")
        print(f"   Description: {improvement['description']}")
        print(f"   Affected: {', '.join(improvement['affected_topics'][:5])}")
        if len(improvement['affected_topics']) > 5:
            print(f"   ... and {len(improvement['affected_topics']) - 5} more")
        print(f"   Action: {improvement['action']}")

    # Generate summary report
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Domains Identified: {len([d for d in domains.keys() if d != 'unknown'])}")
    print(f"Data Products Suggested: {len(suggestions)}")
    print(f"Improvements Recommended: {len(improvements)}")
    print()

    # Save analysis results
    output = {
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "source_inventory": str(inventory_file),
        "domains": {k: {'topic_count': len(set(v['topics'])), 'topics': sorted(set(v['topics']))}
                   for k, v in domains.items()},
        "suggested_data_products": suggestions,
        "recommended_improvements": improvements
    }

    output_file = Path("discovery-outputs") / f"analysis-{datetime.now(UTC).isoformat()}.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        inventory_file = sys.argv[1]
    else:
        # Find the most recent inventory file
        inventory_dir = Path("discovery-outputs")
        inventory_files = sorted(inventory_dir.glob("inventory-*.json"))
        if not inventory_files:
            print("No inventory files found in discovery-outputs/")
            sys.exit(1)
        inventory_file = inventory_files[-1]

    print(f"Analyzing: {inventory_file}\n")
    analyze_inventory(inventory_file)
