# Real-Time Gaming Intelligence Platform

## Overview

The Real-Time Gaming Intelligence Platform is a data product that aggregates and enriches gaming data from multiple sources to provide comprehensive real-time insights into player behavior, game performance, and revenue metrics. This platform combines player activity events with game metadata and player profiles to create a unified intelligence stream for analytics, monitoring, and decision-making.

**Domain**: Gaming
**Owner**: data-mesh-team
**Classification**: INTERNAL
**Processing Engine**: ksqlDB

## Business Value

This data product enables:

- **Real-time player behavior analysis**: Track player engagement, session patterns, and performance metrics as they happen
- **Revenue optimization**: Monitor in-game purchases and identify high-value player segments
- **Game performance monitoring**: Analyze active player counts, session durations, and engagement by game/genre
- **Personalization opportunities**: Segment players by performance level and behavior for targeted experiences
- **Operational insights**: Detect anomalies in player activity and game performance in real-time

## Architecture

### Source Topics

The platform aggregates data from three source topics:

1. **gaming_games** - Game metadata (name, genre, publisher, platform, rating)
2. **gaming_players** - Player profiles (username, email, level, country, account status)
3. **gaming_player_activity** - Activity events (sessions, scores, achievements, purchases)

### Output Topic

**Topic Name**: `gaming.real-time-gaming-intelligence-platform`
**Partitions**: 6
**Retention**: 7 days (604800000 ms)
**Format**: Avro

### Data Flow

```
┌─────────────────┐
│ gaming_games    │───┐
└─────────────────┘   │
                      │    ┌──────────────────┐
┌─────────────────┐   ├───▶│ ksqlDB Processing│
│ gaming_players  │───┤    │  - Enrichment    │
└─────────────────┘   │    │  - Aggregation   │
                      │    │  - Windowing     │
┌─────────────────┐   │    └────────┬─────────┘
│ gaming_player_  │───┘             │
│   activity      │                 │
└─────────────────┘                 │
                                    ▼
                    ┌───────────────────────────────┐
                    │ gaming.real-time-gaming-      │
                    │   intelligence-platform       │
                    │ (Enriched Intelligence Stream)│
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌──────────────────────┐      ┌────────────────────────┐
        │ Analytics Dashboards │      │  ML/AI Applications    │
        │ - Grafana            │      │  - Player Segmentation │
        │ - Tableau            │      │  - Churn Prediction    │
        └──────────────────────┘      └────────────────────────┘
```

### Processing Logic

1. **Stream Creation**: Create base streams from source topics with proper schema mapping
2. **Table Materialization**: Build tables for reference data (latest game/player info)
3. **Stream Enrichment**: Join activity events with player and game data
4. **Windowed Aggregations**: Calculate metrics over time windows (1 hour, 5 minutes)
5. **Intelligence Stream**: Produce enriched events with derived attributes
6. **Analytics Views**: Create additional tables for specific analytics use cases

## Schema

### Output Schema (Avro)

```json
{
  "type": "record",
  "name": "GamingIntelligence",
  "namespace": "com.datamesh.gaming",
  "fields": [
    {"name": "game_id", "type": "string"},
    {"name": "game_name", "type": ["null", "string"]},
    {"name": "game_genre", "type": ["null", "string"]},
    {"name": "player_id", "type": "string"},
    {"name": "player_username", "type": ["null", "string"]},
    {"name": "player_email", "type": ["null", "string"]},
    {"name": "player_level", "type": ["null", "int"]},
    {"name": "activity_type", "type": "string"},
    {"name": "session_id", "type": ["null", "string"]},
    {"name": "score", "type": ["null", "long"]},
    {"name": "duration_seconds", "type": ["null", "int"]},
    {"name": "total_sessions_1h", "type": ["null", "long"]},
    {"name": "avg_score_1h", "type": ["null", "double"]},
    {"name": "active_players_count", "type": ["null", "long"]},
    {"name": "event_timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "processing_timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}}
  ]
}
```

## Deployment

### Prerequisites

1. Confluent Cloud environment with:
   - Kafka cluster (Standard tier or higher for RBAC)
   - Schema Registry with Stream Governance
   - ksqlDB cluster (provisioned with adequate CSUs)

2. Source topics must exist and contain data:
   - `gaming_games`
   - `gaming_players`
   - `gaming_player_activity`

3. Terraform installed (v1.0+)

4. Confluent Cloud credentials configured

### Step 1: Deploy Infrastructure with Terraform

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform (if not already done)
terraform init

# Set required variables (create terraform.tfvars or use environment variables)
export TF_VAR_cluster_id="lkc-xxxxx"
export TF_VAR_environment_id="env-xxxxx"
export TF_VAR_schema_registry_cluster_id="lsrc-xxxxx"
export TF_VAR_cluster_admin_api_key_id="your-api-key-id"

# Preview changes
terraform plan -target=module.data-products

# Apply configuration
terraform apply -target=module.data-products
```

This will create:
- Service account: `gaming-intelligence-platform-sa`
- Output topic: `gaming.real-time-gaming-intelligence-platform`
- Avro schema registration
- RBAC role bindings for source topic access
- API keys for Kafka and Schema Registry

### Step 2: Deploy ksqlDB Queries

```bash
# Connect to your ksqlDB cluster
# Option 1: Via Confluent Cloud UI
# - Navigate to ksqlDB in Confluent Cloud
# - Open your ksqlDB cluster
# - Copy and paste queries from queries/real-time-gaming-intelligence-platform.sql

# Option 2: Via ksqlDB CLI
ksql http://your-ksqldb-endpoint:8088

# Run the SQL file
RUN SCRIPT 'queries/real-time-gaming-intelligence-platform.sql';
```

### Step 3: Verify Deployment

```bash
# Get connection details
terraform output gaming_intelligence_deployment_info

# Check topic creation
confluent kafka topic describe gaming.real-time-gaming-intelligence-platform

# Verify data is flowing (via ksqlDB)
SELECT * FROM gaming_real_time_intelligence_platform EMIT CHANGES LIMIT 5;

# Check record count
SELECT COUNT(*) AS record_count
FROM gaming_real_time_intelligence_platform
EMIT CHANGES;
```

## Usage Examples

### Query Patterns

#### 1. Monitor Real-Time Player Activity

```sql
-- View enriched activity events as they arrive
SELECT
    game_name,
    player_username,
    activity_type,
    score,
    duration_seconds
FROM gaming_real_time_intelligence_platform
EMIT CHANGES;
```

#### 2. Track High-Value Players

```sql
-- Find players with in-game purchases
SELECT
    player_id,
    player_username,
    game_name,
    SUM(in_game_purchases) AS total_spent
FROM gaming_real_time_intelligence_platform
WHERE has_purchase = true
WINDOW TUMBLING (SIZE 24 HOURS)
GROUP BY player_id, player_username, game_name
EMIT CHANGES;
```

#### 3. Game Performance Metrics

```sql
-- Active players per game (5-minute windows)
SELECT
    game_id,
    game_name,
    active_players_count,
    total_activities,
    avg_session_duration
FROM gaming_active_players_5min
EMIT CHANGES;
```

#### 4. Player Segmentation

```sql
-- Segment players by performance level
SELECT
    player_segment,
    COUNT_DISTINCT(player_id) AS player_count,
    AVG(score) AS avg_score,
    AVG(duration_seconds) AS avg_session_duration
FROM gaming_real_time_intelligence_platform
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY player_segment
EMIT CHANGES;
```

#### 5. Revenue Analytics

```sql
-- Hourly revenue by game
SELECT
    game_name,
    unique_paying_users,
    total_revenue,
    avg_purchase_value,
    total_purchase_events
FROM gaming_revenue_analytics
EMIT CHANGES;
```

#### 6. Genre Analysis

```sql
-- Engagement metrics by game genre
SELECT
    game_genre,
    unique_players,
    total_activities,
    avg_session_duration,
    total_achievements
FROM gaming_genre_engagement
EMIT CHANGES;
```

### Consumer Applications

#### Python Consumer Example

```python
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

# Configuration
config = {
    'bootstrap.servers': 'pkc-xxxxx.us-east-1.aws.confluent.cloud:9092',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': 'YOUR_API_KEY',
    'sasl.password': 'YOUR_API_SECRET',
    'group.id': 'gaming-intelligence-consumer',
    'auto.offset.reset': 'earliest'
}

sr_config = {
    'url': 'https://psrc-xxxxx.us-east-1.aws.confluent.cloud',
    'basic.auth.user.info': 'SR_API_KEY:SR_API_SECRET'
}

# Initialize Schema Registry client
sr_client = SchemaRegistryClient(sr_config)

# Get schema
subject_name = 'gaming.real-time-gaming-intelligence-platform-value'
schema_str = sr_client.get_latest_version(subject_name).schema.schema_str

# Create Avro deserializer
avro_deserializer = AvroDeserializer(sr_client, schema_str)

# Create consumer
consumer = Consumer(config)
consumer.subscribe(['gaming.real-time-gaming-intelligence-platform'])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        # Deserialize value
        value = avro_deserializer(
            msg.value(),
            SerializationContext(msg.topic(), MessageField.VALUE)
        )

        print(f"Received event:")
        print(f"  Game: {value['game_name']}")
        print(f"  Player: {value['player_username']}")
        print(f"  Activity: {value['activity_type']}")
        print(f"  Score: {value['score']}")
        print(f"  Duration: {value['duration_seconds']}s")
        print()

except KeyboardInterrupt:
    pass
finally:
    consumer.close()
```

## Monitoring

### Key Metrics to Monitor

1. **Throughput**: Messages/second on output topic
2. **Latency**: Processing time (processing_timestamp - event_timestamp)
3. **Consumer Lag**: Lag for downstream consumers
4. **Data Quality**: Null rates for enriched fields
5. **ksqlDB Health**: Query status, processing failures

### Monitoring Queries

```sql
-- Check processing lag
SELECT
    game_id,
    game_name,
    COUNT(*) AS event_count,
    MAX(UNIX_TIMESTAMP() - event_timestamp) AS max_lag_ms,
    AVG(UNIX_TIMESTAMP() - event_timestamp) AS avg_lag_ms
FROM gaming_real_time_intelligence_platform
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY game_id, game_name
EMIT CHANGES;

-- Data quality check
SELECT
    COUNT(*) AS total_records,
    COUNT(game_name) AS records_with_game_name,
    COUNT(player_username) AS records_with_username,
    (COUNT(game_name) * 100.0 / COUNT(*)) AS game_enrichment_rate,
    (COUNT(player_username) * 100.0 / COUNT(*)) AS player_enrichment_rate
FROM gaming_real_time_intelligence_platform
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY 1
EMIT CHANGES;
```

### Confluent Cloud Metrics

Monitor via Confluent Cloud UI:
- Topic throughput and storage
- Consumer group lag
- ksqlDB cluster CPU/memory usage
- Schema Registry requests

## Governance

### Data Classification

- **Classification**: INTERNAL
- **Sensitivity**: Contains player email addresses (PII)
- **Compliance**: Subject to data retention and privacy policies

### Access Control

Access is managed via Confluent Cloud RBAC:

- **Service Account**: `gaming-intelligence-platform-sa`
- **Read Access**: `gaming_games`, `gaming_players`, `gaming_player_activity`
- **Write Access**: `gaming.real-time-gaming-intelligence-platform`
- **Consumer Groups**: `gaming-intelligence-*`

### Data Retention

- **Retention Period**: 7 days
- **Rationale**: Balances analytical needs with storage costs
- **Compliance**: Meets data minimization requirements

### Tags

Topics are tagged for discoverability:
- `gaming`
- `data-product`
- `real-time`
- `enriched`

## Troubleshooting

### Issue: No data in output topic

**Diagnosis**:
```sql
-- Check if source streams are receiving data
SELECT * FROM gaming_player_activity_stream EMIT CHANGES LIMIT 5;
SELECT * FROM gaming_games_stream EMIT CHANGES LIMIT 5;
SELECT * FROM gaming_players_stream EMIT CHANGES LIMIT 5;
```

**Solutions**:
1. Verify source topics contain data
2. Check ksqlDB query status in Confluent Cloud UI
3. Verify RBAC permissions for service account

### Issue: Missing enriched fields (nulls)

**Diagnosis**:
```sql
-- Check join success rates
SELECT
    COUNT(*) AS total,
    COUNT(game_name) AS with_game,
    COUNT(player_username) AS with_player
FROM gaming_activity_enriched
EMIT CHANGES
LIMIT 100;
```

**Solutions**:
1. Ensure reference tables are populated (gaming_games_table, gaming_players_table)
2. Check for key mismatches between activity and reference data
3. Verify Schema Registry compatibility

### Issue: High processing lag

**Diagnosis**:
```sql
-- Check lag metrics
SELECT
    MAX(UNIX_TIMESTAMP() - event_timestamp) AS max_lag_ms
FROM gaming_real_time_intelligence_platform
EMIT CHANGES;
```

**Solutions**:
1. Scale up ksqlDB cluster (increase CSUs)
2. Optimize queries (reduce unnecessary aggregations)
3. Increase topic partitions if needed

### Issue: Consumer lag building up

**Solutions**:
1. Scale consumer application (increase parallelism)
2. Check consumer processing logic for bottlenecks
3. Verify network connectivity to Confluent Cloud

## Cost Optimization

### ksqlDB Cluster Sizing

- **Development**: 4 CSUs (suitable for testing)
- **Production**: 8-12 CSUs (recommended for 100+ events/sec)
- **Scale**: Monitor CSU utilization and scale as needed

### Topic Configuration

Current settings balance performance and cost:
- **Partitions**: 6 (allows parallel processing)
- **Retention**: 7 days (adjust based on downstream needs)
- **Compression**: Snappy (good balance of speed and compression)

### Optimization Tips

1. Use `EMIT CHANGES` judiciously (avoid unnecessary continuous queries)
2. Leverage windowed aggregations instead of unbounded queries
3. Consider reducing retention for intermediate topics
4. Monitor and tune consumer applications for efficiency

## Future Enhancements

Potential improvements to consider:

1. **Machine Learning Integration**: Add real-time anomaly detection for player behavior
2. **Predictive Analytics**: Implement churn prediction models
3. **Enhanced Segmentation**: Add more sophisticated player segmentation logic
4. **Cross-Game Analytics**: Aggregate player behavior across multiple games
5. **Real-Time Recommendations**: Build recommendation engine for in-game offers
6. **Alerting**: Implement real-time alerts for KPI thresholds
7. **Data Quality Monitoring**: Add automated data quality checks and alerts

## Support

For issues, questions, or feature requests:

- **Owner**: data-mesh-team
- **Slack Channel**: #data-mesh-gaming
- **Email**: data-mesh-team@company.com
- **Repository**: [Link to repo]

## References

- [Confluent ksqlDB Documentation](https://docs.confluent.io/cloud/current/ksqldb/index.html)
- [Avro Schema Documentation](https://avro.apache.org/docs/current/)
- [Confluent Cloud RBAC](https://docs.confluent.io/cloud/current/access-management/access-control/rbac/overview.html)
- [Data Mesh Principles](https://martinfowler.com/articles/data-mesh-principles.html)
