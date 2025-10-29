-- ============================================================================
-- Real-Time Gaming Intelligence Platform - ksqlDB Queries
-- ============================================================================
-- Domain: gaming
-- Owner: data-mesh-team
-- Classification: INTERNAL
--
-- This file contains all ksqlDB queries for the Real-Time Gaming Intelligence
-- Platform data product. The queries aggregate data from three source topics:
-- - gaming_games: Game catalog and metadata
-- - gaming_players: Player profiles and account information
-- - gaming_player_activity: Real-time player actions and events
--
-- Prerequisites:
-- 1. ksqlDB cluster must be running
-- 2. Source topics must exist and contain data
-- 3. Execute queries in order (streams before tables, then materialized views)
-- ============================================================================

-- Set query properties for production use
SET 'auto.offset.reset' = 'earliest';
SET 'processing.guarantee' = 'exactly_once';

-- ============================================================================
-- Step 1: Create Streams from Source Topics
-- ============================================================================

-- Stream for gaming_games topic
-- Contains game catalog information and metadata
CREATE STREAM IF NOT EXISTS gaming_games_stream (
    game_id VARCHAR KEY,
    game_name VARCHAR,
    game_type VARCHAR,
    genre VARCHAR,
    platform VARCHAR,
    release_date BIGINT,
    publisher VARCHAR,
    rating DOUBLE,
    max_players INT
) WITH (
    KAFKA_TOPIC='gaming_games',
    VALUE_FORMAT='AVRO',
    TIMESTAMP='release_date'
);

-- Stream for gaming_players topic
-- Contains player profile and account information
CREATE STREAM IF NOT EXISTS gaming_players_stream (
    player_id VARCHAR KEY,
    username VARCHAR,
    email VARCHAR,
    country VARCHAR,
    registration_date BIGINT,
    account_status VARCHAR,
    subscription_tier VARCHAR,
    total_playtime_hours DOUBLE,
    level INT,
    experience_points BIGINT
) WITH (
    KAFKA_TOPIC='gaming_players',
    VALUE_FORMAT='AVRO',
    TIMESTAMP='registration_date'
);

-- Stream for gaming_player_activity topic
-- Contains real-time player actions and gameplay events
CREATE STREAM IF NOT EXISTS gaming_player_activity_stream (
    activity_id VARCHAR KEY,
    player_id VARCHAR,
    game_id VARCHAR,
    activity_type VARCHAR,
    activity_timestamp BIGINT,
    session_id VARCHAR,
    duration_seconds INT,
    score INT,
    level_reached INT,
    achievements_unlocked INT,
    items_purchased INT,
    currency_spent DOUBLE,
    currency_earned DOUBLE
) WITH (
    KAFKA_TOPIC='gaming_player_activity',
    VALUE_FORMAT='AVRO',
    TIMESTAMP='activity_timestamp'
);

-- ============================================================================
-- Step 2: Create Rekeyed Streams for Joins
-- ============================================================================

-- Rekey player activity by player_id for joining with players
CREATE STREAM IF NOT EXISTS gaming_activity_by_player
    WITH (
        KAFKA_TOPIC='gaming_activity_by_player',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    player_id,
    activity_id,
    game_id,
    activity_type,
    activity_timestamp,
    session_id,
    duration_seconds,
    score,
    level_reached,
    achievements_unlocked,
    items_purchased,
    currency_spent,
    currency_earned
FROM gaming_player_activity_stream
PARTITION BY player_id
EMIT CHANGES;

-- Rekey player activity by game_id for joining with games
CREATE STREAM IF NOT EXISTS gaming_activity_by_game
    WITH (
        KAFKA_TOPIC='gaming_activity_by_game',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    game_id,
    activity_id,
    player_id,
    activity_type,
    activity_timestamp,
    session_id,
    duration_seconds,
    score,
    level_reached,
    achievements_unlocked,
    items_purchased,
    currency_spent,
    currency_earned
FROM gaming_player_activity_stream
PARTITION BY game_id
EMIT CHANGES;

-- ============================================================================
-- Step 3: Create Tables for State Management
-- ============================================================================

-- Table for current game state (latest information per game)
CREATE TABLE IF NOT EXISTS gaming_games_table (
    game_id VARCHAR PRIMARY KEY,
    game_name VARCHAR,
    game_type VARCHAR,
    genre VARCHAR,
    platform VARCHAR,
    release_date BIGINT,
    publisher VARCHAR,
    rating DOUBLE,
    max_players INT
) WITH (
    KAFKA_TOPIC='gaming_games',
    VALUE_FORMAT='AVRO'
);

-- Table for current player state (latest information per player)
CREATE TABLE IF NOT EXISTS gaming_players_table (
    player_id VARCHAR PRIMARY KEY,
    username VARCHAR,
    email VARCHAR,
    country VARCHAR,
    registration_date BIGINT,
    account_status VARCHAR,
    subscription_tier VARCHAR,
    total_playtime_hours DOUBLE,
    level INT,
    experience_points BIGINT
) WITH (
    KAFKA_TOPIC='gaming_players',
    VALUE_FORMAT='AVRO'
);

-- ============================================================================
-- Step 4: Create Enriched Activity Stream (Player + Game Context)
-- ============================================================================

-- Join activity with player and game information for full context
CREATE STREAM IF NOT EXISTS gaming_enriched_activity
    WITH (
        KAFKA_TOPIC='gaming_enriched_activity',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    a.activity_id,
    a.player_id,
    p.username,
    p.country AS player_country,
    p.subscription_tier,
    p.level AS player_level,
    a.game_id,
    g.game_name,
    g.genre,
    g.platform,
    g.publisher,
    a.activity_type,
    a.activity_timestamp,
    a.session_id,
    a.duration_seconds,
    a.score,
    a.level_reached,
    a.achievements_unlocked,
    a.items_purchased,
    a.currency_spent,
    a.currency_earned,
    (a.currency_earned - a.currency_spent) AS net_currency_change
FROM gaming_activity_by_player a
LEFT JOIN gaming_players_table p ON a.player_id = p.player_id
LEFT JOIN gaming_games_table g ON a.game_id = g.game_id
EMIT CHANGES;

-- ============================================================================
-- Step 5: Create Aggregated Analytics Tables
-- ============================================================================

-- Real-time player statistics (5-minute tumbling window)
CREATE TABLE IF NOT EXISTS gaming_player_stats_5min
    WITH (
        KAFKA_TOPIC='gaming_player_stats_5min',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    player_id,
    username,
    player_country,
    subscription_tier,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    COUNT(*) AS activity_count,
    COUNT_DISTINCT(game_id) AS unique_games_played,
    COUNT_DISTINCT(session_id) AS session_count,
    SUM(duration_seconds) AS total_duration_seconds,
    AVG(duration_seconds) AS avg_duration_seconds,
    SUM(score) AS total_score,
    AVG(score) AS avg_score,
    MAX(level_reached) AS max_level_reached,
    SUM(achievements_unlocked) AS total_achievements,
    SUM(items_purchased) AS total_items_purchased,
    SUM(currency_spent) AS total_currency_spent,
    SUM(currency_earned) AS total_currency_earned,
    SUM(net_currency_change) AS net_currency_change
FROM gaming_enriched_activity
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY player_id, username, player_country, subscription_tier
EMIT CHANGES;

-- Real-time game statistics (5-minute tumbling window)
CREATE TABLE IF NOT EXISTS gaming_game_stats_5min
    WITH (
        KAFKA_TOPIC='gaming_game_stats_5min',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    game_id,
    game_name,
    genre,
    platform,
    publisher,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    COUNT(*) AS activity_count,
    COUNT_DISTINCT(player_id) AS unique_players,
    COUNT_DISTINCT(session_id) AS session_count,
    SUM(duration_seconds) AS total_playtime_seconds,
    AVG(duration_seconds) AS avg_session_duration,
    AVG(score) AS avg_score,
    MAX(score) AS max_score,
    SUM(achievements_unlocked) AS total_achievements,
    SUM(items_purchased) AS total_items_purchased,
    SUM(currency_spent) AS total_revenue,
    AVG(currency_spent) AS avg_revenue_per_session
FROM gaming_enriched_activity
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY game_id, game_name, genre, platform, publisher
EMIT CHANGES;

-- Real-time genre performance (5-minute tumbling window)
CREATE TABLE IF NOT EXISTS gaming_genre_stats_5min
    WITH (
        KAFKA_TOPIC='gaming_genre_stats_5min',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    genre,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    COUNT(*) AS activity_count,
    COUNT_DISTINCT(player_id) AS unique_players,
    COUNT_DISTINCT(game_id) AS active_games,
    SUM(duration_seconds) AS total_playtime_seconds,
    AVG(duration_seconds) AS avg_session_duration,
    SUM(currency_spent) AS total_revenue,
    AVG(currency_spent) AS avg_revenue_per_activity
FROM gaming_enriched_activity
WHERE genre IS NOT NULL
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY genre
EMIT CHANGES;

-- ============================================================================
-- Step 6: Create Main Data Product Stream
-- ============================================================================

-- Final aggregated data product combining all intelligence
-- This stream feeds the gaming.real-time-gaming-intelligence-platform topic
CREATE STREAM IF NOT EXISTS gaming_intelligence_platform
    WITH (
        KAFKA_TOPIC='gaming.real-time-gaming-intelligence-platform',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6,
        REPLICAS=3
    ) AS
SELECT
    CONCAT(CAST(ps.player_id AS STRING), '_', CAST(gs.game_id AS STRING), '_', CAST(WINDOWSTART AS STRING)) AS intelligence_key,
    -- Player dimensions
    ps.player_id,
    ps.username,
    ps.player_country,
    ps.subscription_tier,
    -- Game dimensions
    gs.game_id,
    gs.game_name,
    gs.genre,
    gs.platform,
    gs.publisher,
    -- Time dimensions
    ps.window_start AS window_start_timestamp,
    ps.window_end AS window_end_timestamp,
    -- Player metrics
    ps.activity_count AS player_activity_count,
    ps.unique_games_played,
    ps.session_count AS player_session_count,
    ps.total_duration_seconds AS player_total_duration,
    ps.avg_duration_seconds AS player_avg_duration,
    ps.total_score AS player_total_score,
    ps.avg_score AS player_avg_score,
    ps.max_level_reached AS player_max_level,
    ps.total_achievements AS player_achievements,
    ps.total_items_purchased AS player_items_purchased,
    ps.total_currency_spent AS player_currency_spent,
    ps.total_currency_earned AS player_currency_earned,
    ps.net_currency_change AS player_net_currency,
    -- Game metrics
    gs.activity_count AS game_activity_count,
    gs.unique_players AS game_unique_players,
    gs.session_count AS game_session_count,
    gs.total_playtime_seconds AS game_total_playtime,
    gs.avg_session_duration AS game_avg_session_duration,
    gs.avg_score AS game_avg_score,
    gs.max_score AS game_max_score,
    gs.total_achievements AS game_achievements_unlocked,
    gs.total_items_purchased AS game_items_purchased,
    gs.total_revenue AS game_revenue,
    gs.avg_revenue_per_session AS game_avg_revenue_per_session,
    -- Engagement score (composite metric)
    (ps.activity_count * 0.3 +
     ps.total_duration_seconds / 60.0 * 0.3 +
     ps.total_score / 100.0 * 0.2 +
     ps.total_achievements * 0.2) AS player_engagement_score,
    -- Monetization rate
    CASE
        WHEN ps.activity_count > 0
        THEN (CAST(ps.total_items_purchased AS DOUBLE) / ps.activity_count) * 100
        ELSE 0.0
    END AS player_monetization_rate_pct,
    -- Game popularity score
    (gs.unique_players * 0.4 +
     gs.total_playtime_seconds / 3600.0 * 0.3 +
     gs.total_revenue * 0.3) AS game_popularity_score
FROM gaming_player_stats_5min ps
INNER JOIN gaming_game_stats_5min gs
    WITHIN 5 MINUTES
    ON ps.window_start = gs.window_start
EMIT CHANGES;

-- ============================================================================
-- Step 7: Create Alerting Streams (High-Value Events)
-- ============================================================================

-- High-value player activity alert (spending > $100 in 5 minutes)
CREATE STREAM IF NOT EXISTS gaming_high_value_player_alert
    WITH (
        KAFKA_TOPIC='gaming_high_value_player_alert',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    player_id,
    username,
    player_country,
    subscription_tier,
    window_start,
    window_end,
    total_currency_spent,
    total_items_purchased,
    'HIGH_SPENDING' AS alert_type,
    'Player spent over $100 in 5-minute window' AS alert_description
FROM gaming_player_stats_5min
WHERE total_currency_spent > 100
EMIT CHANGES;

-- Churn risk alert (low engagement in recent window)
CREATE STREAM IF NOT EXISTS gaming_churn_risk_alert
    WITH (
        KAFKA_TOPIC='gaming_churn_risk_alert',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    player_id,
    username,
    player_country,
    subscription_tier,
    window_start,
    window_end,
    activity_count,
    total_duration_seconds,
    'CHURN_RISK' AS alert_type,
    'Player showing low engagement' AS alert_description
FROM gaming_player_stats_5min
WHERE subscription_tier IN ('PREMIUM', 'VIP')
  AND activity_count < 2
  AND total_duration_seconds < 300
EMIT CHANGES;

-- Popular game alert (high concurrent players)
CREATE STREAM IF NOT EXISTS gaming_popular_game_alert
    WITH (
        KAFKA_TOPIC='gaming_popular_game_alert',
        VALUE_FORMAT='AVRO',
        PARTITIONS=6
    ) AS
SELECT
    game_id,
    game_name,
    genre,
    platform,
    window_start,
    window_end,
    unique_players,
    total_revenue,
    'TRENDING_GAME' AS alert_type,
    'Game experiencing high player activity' AS alert_description
FROM gaming_game_stats_5min
WHERE unique_players > 50
EMIT CHANGES;

-- ============================================================================
-- Helpful Queries for Monitoring and Troubleshooting
-- ============================================================================

-- Check stream processing
-- SELECT * FROM gaming_enriched_activity EMIT CHANGES LIMIT 10;

-- Check player statistics
-- SELECT * FROM gaming_player_stats_5min EMIT CHANGES LIMIT 10;

-- Check game statistics
-- SELECT * FROM gaming_game_stats_5min EMIT CHANGES LIMIT 10;

-- Check final data product
-- SELECT * FROM gaming_intelligence_platform EMIT CHANGES LIMIT 10;

-- Check alerts
-- SELECT * FROM gaming_high_value_player_alert EMIT CHANGES;
-- SELECT * FROM gaming_churn_risk_alert EMIT CHANGES;
-- SELECT * FROM gaming_popular_game_alert EMIT CHANGES;

-- Describe streams and tables
-- DESCRIBE gaming_enriched_activity;
-- DESCRIBE gaming_player_stats_5min;
-- DESCRIBE gaming_intelligence_platform;

-- Show running queries
-- SHOW QUERIES;

-- Explain query execution plan
-- EXPLAIN <query_id>;
