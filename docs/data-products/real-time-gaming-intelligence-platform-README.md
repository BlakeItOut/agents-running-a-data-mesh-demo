# Real-Time Gaming Intelligence Platform

## Overview

The Real-Time Gaming Intelligence Platform is a production-ready data product that aggregates and enriches gaming data from multiple sources to provide comprehensive, real-time analytics for game performance monitoring, player behavior tracking, and business intelligence.

**Domain**: Gaming
**Owner**: data-mesh-team
**Classification**: INTERNAL
**Retention Policy**: 7 days
**Processing Engine**: ksqlDB

## Business Value

This data product enables:

- **Real-time Player Analytics**: Track player engagement, behavior patterns, and monetization metrics across all games
- **Game Performance Monitoring**: Monitor game popularity, player retention, and revenue generation in real-time
- **Churn Prevention**: Identify at-risk players with low engagement patterns for proactive retention campaigns
- **Revenue Optimization**: Detect high-value players and optimize in-game purchase opportunities
- **Trend Detection**: Identify trending games and genres to inform marketing and development priorities
- **Cross-game Insights**: Analyze player behavior across multiple games for personalized recommendations

## Architecture

### Source Topics

The platform aggregates data from three source topics:

1. **gaming_games** (Game Catalog)
   - Game metadata, genre, platform, publisher information
   - Release dates and ratings
   - Maximum player capacity

2. **gaming_players** (Player Profiles)
   - Player account information
   - Subscription tiers and account status
   - Player level and experience points
   - Total playtime hours

3. **gaming_player_activity** (Real-time Events)
   - Player actions and gameplay events
   - Session information and duration
   - Scores, achievements, level progression
   - In-game purchases and currency transactions

### Output Topic

**Topic Name**: `gaming.real-time-gaming-intelligence-platform`
**Partitions**: 6
**Retention**: 7 days (604800000 ms)
**Compression**: Snappy
**Replication**: 3 (min.insync.replicas=2)

### Data Flow

```
gaming_games ────────┐
                     │
gaming_players ──────┤──> ksqlDB Processing ──> gaming.real-time-gaming-intelligence-platform
                     │         │
gaming_player_activity┘        │
                               ├──> gaming_high_value_player_alert
                               ├──> gaming_churn_risk_alert
                               └──> gaming_popular_game_alert
```

### Processing Logic

The ksqlDB application performs the following transformations:

1. **Stream Creation**: Creates streams from all three source topics
2. **Rekeying**: Repartitions activity data by player_id and game_id for efficient joins
3. **State Management**: Maintains current state tables for games and players
4. **Enrichment**: Joins activity events with player and game context
5. **Windowed Aggregation**: Calculates 5-minute tumbling window statistics for:
   - Per-player metrics (engagement, spending, performance)
   - Per-game metrics (popularity, revenue, player count)
   - Per-genre metrics (category performance)
6. **Final Integration**: Combines player and game statistics into unified intelligence records
7. **Alert Generation**: Produces real-time alerts for high-value events

## Data Schema

### Output Record Structure

```json
{
  "intelligence_key": "player123_game456_1234567890000",

  "player_id": "player123",
  "username": "ProGamer42",
  "player_country": "US",
  "subscription_tier": "PREMIUM",

  "game_id": "game456",
  "game_name": "Space Warriors",
  "genre": "Action",
  "platform": "PC",
  "publisher": "Epic Games Inc",

  "window_start_timestamp": 1234567800000,
  "window_end_timestamp": 1234568100000,

  "player_activity_count": 15,
  "unique_games_played": 1,
  "player_session_count": 3,
  "player_total_duration": 3600,
  "player_avg_duration": 240,
  "player_total_score": 15000,
  "player_avg_score": 1000,
  "player_max_level": 12,
  "player_achievements": 5,
  "player_items_purchased": 3,
  "player_currency_spent": 45.99,
  "player_currency_earned": 120.00,
  "player_net_currency": 74.01,

  "game_activity_count": 450,
  "game_unique_players": 87,
  "game_session_count": 125,
  "game_total_playtime": 108000,
  "game_avg_session_duration": 864,
  "game_avg_score": 950,
  "game_max_score": 25000,
  "game_achievements_unlocked": 234,
  "game_items_purchased": 156,
  "game_revenue": 2345.67,
  "game_avg_revenue_per_session": 18.76,

  "player_engagement_score": 125.5,
  "player_monetization_rate_pct": 20.0,
  "game_popularity_score": 892.3
}
```

### Key Metrics Explained

**Player Metrics:**
- `player_engagement_score`: Composite score based on activity count (30%), duration (30%), score (20%), and achievements (20%)
- `player_monetization_rate_pct`: Percentage of activities that resulted in purchases
- `player_net_currency`: Net currency change (earned - spent) during the window

**Game Metrics:**
- `game_popularity_score`: Composite score based on unique players (40%), playtime hours (30%), and revenue (30%)
- `game_avg_revenue_per_session`: Average revenue generated per gaming session
- `game_unique_players`: Count of distinct players active in the window

## Deployment

### Prerequisites

1. **Confluent Cloud Environment**
   - Standard Kafka cluster with RBAC enabled
   - Stream Governance (ESSENTIALS) package
   - ksqlDB cluster provisioned

2. **Source Topics**
   - `gaming_games` topic with Avro schema
   - `gaming_players` topic with Avro schema
   - `gaming_player_activity` topic with Avro schema

3. **Terraform**
   - Version >= 1.0
   - Confluent provider ~> 2.0

### Step 1: Deploy Infrastructure

Navigate to the terraform directory and apply the data product configuration:

```bash
cd terraform

# Review the changes
terraform plan -target=module.data_products

# Apply the configuration
terraform apply -target=module.data_products

# Or apply specific data product
terraform apply \
  -target=confluent_kafka_topic.gaming_intelligence_platform \
  -target=confluent_service_account.gaming_intelligence_sa \
  -target=confluent_kafka_acl.gaming_intelligence_read_games \
  -target=confluent_kafka_acl.gaming_intelligence_read_players \
  -target=confluent_kafka_acl.gaming_intelligence_read_activity \
  -target=confluent_kafka_acl.gaming_intelligence_write \
  -target=confluent_kafka_acl.gaming_intelligence_read_product \
  -target=confluent_kafka_acl.gaming_intelligence_consumer_group \
  -target=confluent_api_key.gaming_intelligence_api_key
```

### Step 2: Retrieve Credentials

Get the API credentials for the data product service account:

```bash
# Get API key
terraform output -raw gaming_intelligence_platform_api_key

# Get API secret
terraform output -raw gaming_intelligence_platform_api_secret

# Get topic name
terraform output -raw gaming_intelligence_platform_topic

# Get full info
terraform output gaming_intelligence_platform_info
```

### Step 3: Deploy ksqlDB Queries

Connect to your ksqlDB cluster and execute the queries:

#### Option A: Using Confluent Cloud UI

1. Navigate to Confluent Cloud Console
2. Select your environment and cluster
3. Go to ksqlDB section
4. Select your ksqlDB cluster
5. Open the editor
6. Copy and paste the contents of `queries/real-time-gaming-intelligence-platform.sql`
7. Execute the queries in order

#### Option B: Using ksqlDB CLI

```bash
# Set environment variables
export KSQL_ENDPOINT="your-ksqldb-endpoint"
export KSQL_API_KEY="your-ksqldb-api-key"
export KSQL_API_SECRET="your-ksqldb-api-secret"

# Execute queries using ksqlDB CLI
ksql -u $KSQL_API_KEY -p $KSQL_API_SECRET $KSQL_ENDPOINT \
  < queries/real-time-gaming-intelligence-platform.sql
```

#### Option C: Using REST API

```bash
# Execute queries via REST API
curl -X POST $KSQL_ENDPOINT/ksql \
  -H "Content-Type: application/vnd.ksql.v1+json" \
  -u "$KSQL_API_KEY:$KSQL_API_SECRET" \
  -d @queries/real-time-gaming-intelligence-platform.sql
```

### Step 4: Verify Deployment

Check that all streams and tables are created:

```sql
-- List all streams
SHOW STREAMS;

-- List all tables
SHOW TABLES;

-- List all running queries
SHOW QUERIES;

-- Verify data is flowing
SELECT * FROM gaming_intelligence_platform EMIT CHANGES LIMIT 10;
```

## Usage Examples

### Example 1: Monitor Real-Time Player Engagement

Query the data product topic to see player engagement in real-time:

```sql
SELECT
    player_id,
    username,
    game_name,
    player_engagement_score,
    player_activity_count,
    player_total_duration / 60 AS playtime_minutes,
    player_currency_spent,
    player_monetization_rate_pct
FROM gaming_intelligence_platform
WHERE player_engagement_score > 100
EMIT CHANGES;
```

### Example 2: Identify Top Performing Games

Find games with the highest popularity scores:

```sql
SELECT
    game_id,
    game_name,
    genre,
    game_popularity_score,
    game_unique_players,
    game_revenue,
    game_avg_revenue_per_session
FROM gaming_intelligence_platform
WHERE game_unique_players > 50
ORDER BY game_popularity_score DESC
EMIT CHANGES;
```

### Example 3: Track Genre Performance

Monitor which genres are performing best:

```sql
SELECT
    genre,
    COUNT(*) AS record_count,
    AVG(game_popularity_score) AS avg_popularity,
    SUM(game_revenue) AS total_revenue,
    SUM(game_unique_players) AS total_players
FROM gaming_intelligence_platform
GROUP BY genre
EMIT CHANGES;
```

### Example 4: Detect High-Value Players

Subscribe to high-value player alerts:

```sql
SELECT
    player_id,
    username,
    total_currency_spent,
    total_items_purchased,
    alert_description
FROM gaming_high_value_player_alert
EMIT CHANGES;
```

### Example 5: Monitor Churn Risk

Identify players at risk of churning:

```sql
SELECT
    player_id,
    username,
    subscription_tier,
    activity_count,
    total_duration_seconds / 60 AS duration_minutes,
    alert_description
FROM gaming_churn_risk_alert
EMIT CHANGES;
```

## Consumer Integration

### Python Consumer Example

```python
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

# Configuration
kafka_config = {
    'bootstrap.servers': 'your-cluster.confluent.cloud:9092',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': 'your-api-key',
    'sasl.password': 'your-api-secret',
    'group.id': 'gaming-intelligence-consumer-group',
    'auto.offset.reset': 'latest'
}

schema_registry_config = {
    'url': 'https://your-schema-registry.confluent.cloud',
    'basic.auth.user.info': 'sr-api-key:sr-api-secret'
}

# Create Schema Registry client
schema_registry_client = SchemaRegistryClient(schema_registry_config)

# Create Avro deserializer
avro_deserializer = AvroDeserializer(
    schema_registry_client,
    schema_str=None  # Will fetch schema automatically
)

# Create consumer
consumer = Consumer(kafka_config)
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

        # Process the intelligence record
        print(f"Player: {value['username']}")
        print(f"Game: {value['game_name']}")
        print(f"Engagement Score: {value['player_engagement_score']}")
        print(f"Revenue: ${value['game_revenue']:.2f}")
        print("---")

except KeyboardInterrupt:
    pass
finally:
    consumer.close()
```

### Java Consumer Example

```java
import org.apache.kafka.clients.consumer.*;
import io.confluent.kafka.serializers.KafkaAvroDeserializer;
import java.time.Duration;
import java.util.*;

public class GamingIntelligenceConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG,
                  "your-cluster.confluent.cloud:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG,
                  "gaming-intelligence-consumer-group");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
                  KafkaAvroDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
                  KafkaAvroDeserializer.class.getName());
        props.put("security.protocol", "SASL_SSL");
        props.put("sasl.mechanism", "PLAIN");
        props.put("sasl.jaas.config",
                  "org.apache.kafka.common.security.plain.PlainLoginModule " +
                  "required username='your-api-key' password='your-api-secret';");
        props.put("schema.registry.url",
                  "https://your-schema-registry.confluent.cloud");
        props.put("basic.auth.credentials.source", "USER_INFO");
        props.put("basic.auth.user.info", "sr-api-key:sr-api-secret");

        KafkaConsumer<String, GenericRecord> consumer =
            new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("gaming.real-time-gaming-intelligence-platform"));

        try {
            while (true) {
                ConsumerRecords<String, GenericRecord> records =
                    consumer.poll(Duration.ofMillis(1000));

                for (ConsumerRecord<String, GenericRecord> record : records) {
                    GenericRecord value = record.value();

                    System.out.println("Player: " + value.get("username"));
                    System.out.println("Game: " + value.get("game_name"));
                    System.out.println("Engagement Score: " +
                                     value.get("player_engagement_score"));
                    System.out.println("---");
                }
            }
        } finally {
            consumer.close();
        }
    }
}
```

## Monitoring and Operations

### Key Performance Indicators

Monitor these metrics to ensure healthy operation:

1. **Throughput**
   - Messages per second into output topic
   - Target: > 100 msg/sec during peak hours

2. **Latency**
   - End-to-end processing latency
   - Target: < 5 seconds (p99)

3. **Data Quality**
   - Null value percentage in enriched fields
   - Target: < 5%

4. **Query Performance**
   - ksqlDB query execution time
   - Target: All queries < 10 seconds

### Health Check Queries

```sql
-- Check data freshness (should be within last 5 minutes)
SELECT
    MAX(window_end_timestamp) AS latest_window,
    (UNIX_TIMESTAMP() * 1000) - MAX(window_end_timestamp) AS lag_ms
FROM gaming_intelligence_platform;

-- Check record volume
SELECT
    COUNT(*) AS record_count,
    COUNT(DISTINCT player_id) AS unique_players,
    COUNT(DISTINCT game_id) AS unique_games
FROM gaming_intelligence_platform
WHERE window_start_timestamp > UNIX_TIMESTAMP() * 1000 - 3600000;

-- Check for processing errors
DESCRIBE EXTENDED gaming_intelligence_platform;
```

### Troubleshooting

**Problem**: No data in output topic

1. Check source topics have data:
   ```bash
   kafka-console-consumer --bootstrap-server $KAFKA_ENDPOINT \
     --topic gaming_player_activity --max-messages 10
   ```

2. Verify ksqlDB queries are running:
   ```sql
   SHOW QUERIES;
   EXPLAIN <query_id>;
   ```

3. Check for errors in ksqlDB logs

**Problem**: High latency

1. Check ksqlDB cluster resource utilization
2. Verify partition count matches workload
3. Review windowing configuration (reduce window size if needed)

**Problem**: Missing enrichment data

1. Verify joins are working:
   ```sql
   SELECT * FROM gaming_enriched_activity EMIT CHANGES LIMIT 100;
   ```

2. Check source table populations:
   ```sql
   SELECT COUNT(*) FROM gaming_games_table;
   SELECT COUNT(*) FROM gaming_players_table;
   ```

## Governance

### Data Classification

- **Classification Level**: INTERNAL
- **Contains PII**: Yes (player email, username)
- **Contains Financial Data**: Yes (currency transactions)
- **Compliance Requirements**: GDPR, CCPA

### Access Control

Access to this data product is managed through Confluent Cloud RBAC:

- **Producer**: `gaming-intelligence-sa` service account
- **Consumer**: Request access through data-mesh-team
- **ACLs**: Automatically provisioned via Terraform

### Data Retention

- **Retention Period**: 7 days
- **Rationale**: Balances operational analytics needs with storage costs
- **Extension Process**: Contact data-mesh-team for longer retention requirements

### Tags

This data product is tagged with:
- `gaming`
- `data-product`
- `real-time`
- `analytics`

Search for the topic in Confluent Cloud using these tags.

## Support and Feedback

### Contacts

- **Owner**: data-mesh-team
- **On-Call**: gaming-platform-oncall@company.com
- **Slack Channel**: #gaming-data-products

### Issue Reporting

Report issues via:
1. Jira: PROJECT-GAMING
2. Slack: #gaming-data-products
3. Email: data-mesh-team@company.com

### Enhancement Requests

To request enhancements:
1. Submit feature request in Jira
2. Include business justification and expected usage
3. Tag with `data-product-enhancement`

## Changelog

### Version 1.0.0 (Initial Release)

**Date**: 2024-10-29

**Features**:
- Real-time player engagement tracking
- Game performance monitoring
- Genre-level analytics
- High-value player alerts
- Churn risk detection
- Trending game identification
- 5-minute windowed aggregations
- Composite engagement and popularity scores

**Known Limitations**:
- Historical analysis limited to 7 days
- No session timeout detection
- Monetization metrics assume USD currency

### Roadmap

**Version 1.1.0** (Planned)
- Add hourly and daily aggregation windows
- Include player segment classification
- Add predictive churn scoring
- Support multi-currency conversion

**Version 1.2.0** (Planned)
- Cross-game recommendation engine
- Real-time A/B test analysis integration
- Enhanced fraud detection alerts
- Player lifetime value calculation

## License

Internal use only. Confidential and proprietary to the organization.

---

**Last Updated**: 2024-10-29
**Documentation Version**: 1.0
**Maintained By**: data-mesh-team
