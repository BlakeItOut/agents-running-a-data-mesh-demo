#!/usr/bin/env python3
"""
Update .env file with Kafka/Schema Registry values from Terraform outputs.
Preserves existing Claude API credentials (Anthropic or Bedrock).
"""

import json
import subprocess
import sys
from pathlib import Path


def read_existing_env(env_path):
    """Parse existing .env file and extract Claude-related values."""
    if not env_path.exists():
        return {}

    claude_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Preserve all Claude/Anthropic/Bedrock/AWS related vars
                if key in [
                    'CLAUDE_BACKEND',
                    'ANTHROPIC_API_KEY',
                    'AWS_REGION',
                    'BEDROCK_API_KEY',
                    'AWS_ACCESS_KEY_ID',
                    'AWS_SECRET_ACCESS_KEY'
                ]:
                    claude_vars[key] = value

    return claude_vars


def get_terraform_outputs():
    """Get Kafka and Schema Registry values from Terraform."""
    terraform_dir = Path(__file__).parent.parent / 'terraform'

    try:
        result = subprocess.run(
            ['terraform', 'output', '-json'],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True
        )
        outputs = json.loads(result.stdout)

        return {
            'KAFKA_BOOTSTRAP_ENDPOINT': outputs['kafka_bootstrap_endpoint']['value'],
            'KAFKA_API_KEY': outputs['cluster_admin_api_key']['value'],
            'KAFKA_API_SECRET': outputs['cluster_admin_api_secret']['value'],
            'SCHEMA_REGISTRY_URL': outputs['schema_registry_rest_endpoint']['value'],
            'SCHEMA_REGISTRY_API_KEY': outputs['schema_registry_api_key']['value'],
            'SCHEMA_REGISTRY_API_SECRET': outputs['schema_registry_api_secret']['value']
        }
    except subprocess.CalledProcessError as e:
        print(f"Error running terraform output: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except KeyError as e:
        print(f"Missing expected Terraform output: {e}")
        sys.exit(1)


def write_env_file(env_path, kafka_values, claude_values):
    """Write .env file with merged values."""
    with open(env_path, 'w') as f:
        # Header
        f.write("# Confluent Cloud Kafka Credentials\n")
        f.write(f"KAFKA_BOOTSTRAP_ENDPOINT={kafka_values['KAFKA_BOOTSTRAP_ENDPOINT']}\n")
        f.write(f"KAFKA_API_KEY={kafka_values['KAFKA_API_KEY']}\n")
        f.write(f"KAFKA_API_SECRET={kafka_values['KAFKA_API_SECRET']}\n")
        f.write("\n")

        # MCP Server compatibility aliases
        f.write("# MCP Server expects these names (aliases for compatibility)\n")
        f.write(f"BOOTSTRAP_SERVERS={kafka_values['KAFKA_BOOTSTRAP_ENDPOINT']}\n")
        f.write(f"SASL_USERNAME={kafka_values['KAFKA_API_KEY']}\n")
        f.write(f"SASL_PASSWORD={kafka_values['KAFKA_API_SECRET']}\n")
        f.write("\n")

        # Schema Registry
        f.write("# Schema Registry Credentials\n")
        f.write(f"SCHEMA_REGISTRY_URL={kafka_values['SCHEMA_REGISTRY_URL']}\n")
        f.write(f"SCHEMA_REGISTRY_API_KEY={kafka_values['SCHEMA_REGISTRY_API_KEY']}\n")
        f.write(f"SCHEMA_REGISTRY_API_SECRET={kafka_values['SCHEMA_REGISTRY_API_SECRET']}\n")
        f.write("\n")

        # MCP Server compatibility alias
        f.write("# MCP Server expects this name (alias for compatibility)\n")
        f.write(f"SCHEMA_REGISTRY_ENDPOINT={kafka_values['SCHEMA_REGISTRY_URL']}\n")
        f.write("\n")

        # Claude API Configuration
        f.write("# Claude API Backend Configuration\n")
        f.write("# Options: 'anthropic' (default) or 'bedrock'\n")

        # Preserve or default
        backend = claude_values.get('CLAUDE_BACKEND', 'bedrock')
        f.write(f"CLAUDE_BACKEND={backend}\n")
        f.write("\n")

        # AWS Bedrock Configuration
        f.write("# AWS Bedrock Configuration (if using bedrock backend)\n")
        aws_region = claude_values.get('AWS_REGION', 'us-east-1')
        f.write(f"AWS_REGION={aws_region}\n")

        if 'BEDROCK_API_KEY' in claude_values:
            f.write(f"BEDROCK_API_KEY={claude_values['BEDROCK_API_KEY']}\n")
        else:
            f.write("# BEDROCK_API_KEY=<your-base64-encoded-key>\n")

        if 'AWS_ACCESS_KEY_ID' in claude_values:
            f.write(f"AWS_ACCESS_KEY_ID={claude_values['AWS_ACCESS_KEY_ID']}\n")
            f.write(f"AWS_SECRET_ACCESS_KEY={claude_values.get('AWS_SECRET_ACCESS_KEY', '')}\n")
        else:
            f.write("# AWS_ACCESS_KEY_ID=<your-access-key>\n")
            f.write("# AWS_SECRET_ACCESS_KEY=<your-secret-key>\n")

        f.write("\n")

        # Anthropic Direct API
        f.write("# Anthropic Direct API (if using anthropic backend)\n")
        if 'ANTHROPIC_API_KEY' in claude_values:
            f.write(f"ANTHROPIC_API_KEY={claude_values['ANTHROPIC_API_KEY']}\n")
        else:
            f.write("# ANTHROPIC_API_KEY=sk-ant-...\n")
        f.write("\n")


def main():
    env_path = Path(__file__).parent / '.env'

    print("🔄 Updating .env file from Terraform outputs...")
    print()

    # Step 1: Read existing Claude credentials
    print("1. Reading existing .env for Claude credentials...")
    existing_claude_values = read_existing_env(env_path)
    if existing_claude_values:
        print(f"   ✅ Found {len(existing_claude_values)} existing Claude/AWS variables")
        for key in existing_claude_values.keys():
            # Mask secrets
            if 'KEY' in key or 'SECRET' in key:
                print(f"      - {key}=***")
            else:
                print(f"      - {key}={existing_claude_values[key]}")
    else:
        print("   ⚠️  No existing Claude credentials found")
    print()

    # Step 2: Get Terraform outputs
    print("2. Fetching Kafka/Schema Registry values from Terraform...")
    kafka_values = get_terraform_outputs()
    print("   ✅ Retrieved Terraform outputs")
    print()

    # Step 3: Write merged .env
    print("3. Writing updated .env file...")
    write_env_file(env_path, kafka_values, existing_claude_values)
    print(f"   ✅ Updated {env_path}")
    print()

    print("=" * 70)
    print("✅ .env file updated successfully!")
    print("=" * 70)
    print()
    print("Updated values:")
    print("  • KAFKA_BOOTSTRAP_ENDPOINT")
    print("  • KAFKA_API_KEY")
    print("  • KAFKA_API_SECRET")
    print("  • SCHEMA_REGISTRY_URL")
    print("  • SCHEMA_REGISTRY_API_KEY")
    print("  • SCHEMA_REGISTRY_API_SECRET")
    print()

    if not existing_claude_values:
        print("⚠️  WARNING: No Claude API credentials found!")
        print("   Please add one of the following to .env:")
        print("   - ANTHROPIC_API_KEY (for Anthropic Direct API)")
        print("   - BEDROCK_API_KEY (for AWS Bedrock)")
        print("   - AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY (for AWS IAM auth)")
        print()
    else:
        print("✅ Preserved existing Claude API credentials")
        print()


if __name__ == '__main__':
    main()
