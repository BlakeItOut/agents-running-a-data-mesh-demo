-- ============================================================================
-- Real-Time Gaming Intelligence Platform - ksqlDB Queries
-- ============================================================================
-- Domain: gaming
-- Owner: data-mesh-team
-- Description: Aggregates player activity, game metadata, and player profiles
--              into a unified intelligence stream for real-time analytics
-- Source Topics: gaming_games, gaming_players, gaming_player_activity
-- Output Topic: gaming.real-time-gaming-intelligence-platform
-- ============================================================================

-- Set processing to earliest to capture all data
SET 'auto.offset.reset' = 'earliest';

-- ============================================================================
-- STEP 1: Create base streams from source topics
-- ============================================================================

-- Stream for gaming games (game metadata)
CREATE STREAM IF NOT EXISTS gaming_games_stream (
    game_id VARCHAR KEY,
    game_name VARCHAR,
    genre VARCHAR,
    publisher VARCHAR,
    release_date VARCHAR,
    platform VARCHAR,
    rating DOUBLE,
    price DOUBLE
) WITH (
    KAFKA_TOPIC = 'gaming_games',
    VALUE_FORMAT = 'AVRO',
    TIMESTAMP = 'create_ts'
);

-- Stream for gaming players (player profiles)
CREATE STREAM IF NOT EXISTS gaming_players_stream (
    player_id VARCHAR KEY,
    username VARCHAR,
    email VARCHAR,
    created_date VARCHAR,
    country VARCHAR,
    level INT,
    total_playtime_hours DOUBLE,
    account_status VARCHAR
) WITH (
    KAFKA_TOPIC = 'gaming_players',
    VALUE_FORMAT = 'AVRO',
    TIMESTAMP = 'create_ts'
);

-- Stream for gaming player activity (activity events)
CREATE STREAM IF NOT EXISTS gaming_player_activity_stream (
    activity_id VARCHAR KEY,
    player_id VARCHAR,
    game_id VARCHAR,
    session_id VARCHAR,
    activity_type VARCHAR,
    activity_timestamp BIGINT,
    score BIGINT,
    duration_seconds INT,
    achievements_unlocked INT,
    in_game_purchases DOUBLE
) WITH (
    KAFKA_TOPIC = 'gaming_player_activity',
    VALUE_FORMAT = 'AVRO',
    TIMESTAMP = 'activity_timestamp'
);

-- ============================================================================
-- STEP 2: Create tables for reference data (latest state)
-- ============================================================================

-- Table for current game information
CREATE TABLE IF NOT EXISTS gaming_games_table
WITH (
    KAFKA_TOPIC = 'gaming_games_table',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    game_id,
    LATEST_BY_OFFSET(game_name) AS game_name,
    LATEST_BY_OFFSET(genre) AS genre,
    LATEST_BY_OFFSET(publisher) AS publisher,
    LATEST_BY_OFFSET(platform) AS platform,
    LATEST_BY_OFFSET(rating) AS rating,
    LATEST_BY_OFFSET(price) AS price
FROM gaming_games_stream
GROUP BY game_id
EMIT CHANGES;

-- Table for current player information
CREATE TABLE IF NOT EXISTS gaming_players_table
WITH (
    KAFKA_TOPIC = 'gaming_players_table',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    player_id,
    LATEST_BY_OFFSET(username) AS username,
    LATEST_BY_OFFSET(email) AS email,
    LATEST_BY_OFFSET(country) AS country,
    LATEST_BY_OFFSET(level) AS level,
    LATEST_BY_OFFSET(total_playtime_hours) AS total_playtime_hours,
    LATEST_BY_OFFSET(account_status) AS account_status
FROM gaming_players_stream
GROUP BY player_id
EMIT CHANGES;

-- ============================================================================
-- STEP 3: Enrich activity stream with player and game data
-- ============================================================================

-- Enriched activity stream with player information
CREATE STREAM IF NOT EXISTS gaming_activity_with_player
WITH (
    KAFKA_TOPIC = 'gaming_activity_with_player',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    a.activity_id,
    a.player_id,
    a.game_id,
    a.session_id,
    a.activity_type,
    a.activity_timestamp,
    a.score,
    a.duration_seconds,
    a.achievements_unlocked,
    a.in_game_purchases,
    p.username AS player_username,
    p.email AS player_email,
    p.country AS player_country,
    p.level AS player_level,
    p.account_status AS player_status
FROM gaming_player_activity_stream a
LEFT JOIN gaming_players_table p
    ON a.player_id = p.player_id
EMIT CHANGES;

-- Fully enriched activity stream with both player and game data
CREATE STREAM IF NOT EXISTS gaming_activity_enriched
WITH (
    KAFKA_TOPIC = 'gaming_activity_enriched',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    ap.activity_id,
    ap.player_id,
    ap.game_id,
    ap.session_id,
    ap.activity_type,
    ap.activity_timestamp,
    ap.score,
    ap.duration_seconds,
    ap.achievements_unlocked,
    ap.in_game_purchases,
    ap.player_username,
    ap.player_email,
    ap.player_country,
    ap.player_level,
    ap.player_status,
    g.game_name,
    g.genre AS game_genre,
    g.publisher AS game_publisher,
    g.platform AS game_platform,
    g.rating AS game_rating
FROM gaming_activity_with_player ap
LEFT JOIN gaming_games_table g
    ON ap.game_id = g.game_id
EMIT CHANGES;

-- ============================================================================
-- STEP 4: Create windowed aggregations for real-time metrics
-- ============================================================================

-- Hourly windowed aggregations per player and game
CREATE TABLE IF NOT EXISTS gaming_hourly_player_game_stats
WITH (
    KAFKA_TOPIC = 'gaming_hourly_player_game_stats',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    player_id,
    game_id,
    COUNT(*) AS total_sessions_1h,
    SUM(duration_seconds) AS total_duration_1h,
    AVG(score) AS avg_score_1h,
    MAX(score) AS max_score_1h,
    SUM(achievements_unlocked) AS total_achievements_1h,
    SUM(in_game_purchases) AS total_purchases_1h,
    COUNT_DISTINCT(session_id) AS unique_sessions_1h
FROM gaming_activity_enriched
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY player_id, game_id
EMIT CHANGES;

-- Active player count per game (5-minute windows)
CREATE TABLE IF NOT EXISTS gaming_active_players_5min
WITH (
    KAFKA_TOPIC = 'gaming_active_players_5min',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    game_id,
    COUNT_DISTINCT(player_id) AS active_players_count,
    COUNT(*) AS total_activities,
    AVG(duration_seconds) AS avg_session_duration
FROM gaming_activity_enriched
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY game_id
EMIT CHANGES;

-- ============================================================================
-- STEP 5: Create final unified intelligence stream
-- ============================================================================

-- Main output: Real-Time Gaming Intelligence Platform
CREATE STREAM IF NOT EXISTS gaming_real_time_intelligence_platform
WITH (
    KAFKA_TOPIC = 'gaming.real-time-gaming-intelligence-platform',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6,
    REPLICAS = 3
) AS
SELECT
    e.activity_id,
    e.game_id,
    e.game_name,
    e.game_genre,
    e.game_publisher,
    e.game_platform,
    e.game_rating,
    e.player_id,
    e.player_username,
    e.player_email,
    e.player_country,
    e.player_level,
    e.player_status,
    e.activity_type,
    e.session_id,
    e.score,
    e.duration_seconds,
    e.achievements_unlocked,
    e.in_game_purchases,
    CAST(e.activity_timestamp AS BIGINT) AS event_timestamp,
    CAST(UNIX_TIMESTAMP() AS BIGINT) AS processing_timestamp,
    -- Add contextual metrics
    CASE
        WHEN e.score > 10000 THEN 'HIGH_PERFORMER'
        WHEN e.score > 5000 THEN 'MEDIUM_PERFORMER'
        ELSE 'CASUAL_PLAYER'
    END AS player_segment,
    CASE
        WHEN e.duration_seconds > 3600 THEN 'EXTENDED_SESSION'
        WHEN e.duration_seconds > 1800 THEN 'MEDIUM_SESSION'
        ELSE 'SHORT_SESSION'
    END AS session_type,
    -- Revenue indicator
    CASE
        WHEN e.in_game_purchases > 0 THEN true
        ELSE false
    END AS has_purchase
FROM gaming_activity_enriched e
EMIT CHANGES;

-- ============================================================================
-- STEP 6: Additional analytics views
-- ============================================================================

-- Top performing players (by score) in real-time
CREATE TABLE IF NOT EXISTS gaming_top_performers_hourly
WITH (
    KAFKA_TOPIC = 'gaming_top_performers_hourly',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    game_id,
    player_id,
    player_username,
    SUM(score) AS total_score,
    COUNT(*) AS activity_count,
    MAX(score) AS best_score
FROM gaming_real_time_intelligence_platform
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY game_id, player_id, player_username
HAVING SUM(score) > 1000
EMIT CHANGES;

-- Revenue analytics per game
CREATE TABLE IF NOT EXISTS gaming_revenue_analytics
WITH (
    KAFKA_TOPIC = 'gaming_revenue_analytics',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    game_id,
    game_name,
    COUNT_DISTINCT(player_id) AS unique_paying_users,
    SUM(in_game_purchases) AS total_revenue,
    AVG(in_game_purchases) AS avg_purchase_value,
    COUNT(*) AS total_purchase_events
FROM gaming_real_time_intelligence_platform
WINDOW TUMBLING (SIZE 1 HOUR)
WHERE has_purchase = true
GROUP BY game_id, game_name
EMIT CHANGES;

-- Player engagement by genre
CREATE TABLE IF NOT EXISTS gaming_genre_engagement
WITH (
    KAFKA_TOPIC = 'gaming_genre_engagement',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 6
) AS
SELECT
    game_genre,
    COUNT_DISTINCT(player_id) AS unique_players,
    COUNT(*) AS total_activities,
    AVG(duration_seconds) AS avg_session_duration,
    SUM(achievements_unlocked) AS total_achievements
FROM gaming_real_time_intelligence_platform
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY game_genre
EMIT CHANGES;

-- ============================================================================
-- Queries for monitoring and validation
-- ============================================================================

-- Check record counts
-- SELECT COUNT(*) AS record_count FROM gaming_real_time_intelligence_platform EMIT CHANGES;

-- View sample records
-- SELECT * FROM gaming_real_time_intelligence_platform EMIT CHANGES LIMIT 10;

-- Monitor processing lag
-- SELECT
--     game_id,
--     game_name,
--     COUNT(*) AS event_count,
--     MAX(UNIX_TIMESTAMP() - event_timestamp) AS max_lag_ms
-- FROM gaming_real_time_intelligence_platform
-- WINDOW TUMBLING (SIZE 1 MINUTE)
-- GROUP BY game_id, game_name
-- EMIT CHANGES;

-- ============================================================================
-- Cleanup queries (run to delete resources)
-- ============================================================================

-- DROP STREAM IF EXISTS gaming_real_time_intelligence_platform DELETE TOPIC;
-- DROP TABLE IF EXISTS gaming_genre_engagement DELETE TOPIC;
-- DROP TABLE IF EXISTS gaming_revenue_analytics DELETE TOPIC;
-- DROP TABLE IF EXISTS gaming_top_performers_hourly DELETE TOPIC;
-- DROP TABLE IF EXISTS gaming_active_players_5min DELETE TOPIC;
-- DROP TABLE IF EXISTS gaming_hourly_player_game_stats DELETE TOPIC;
-- DROP STREAM IF EXISTS gaming_activity_enriched DELETE TOPIC;
-- DROP STREAM IF EXISTS gaming_activity_with_player DELETE TOPIC;
-- DROP TABLE IF EXISTS gaming_players_table DELETE TOPIC;
-- DROP TABLE IF EXISTS gaming_games_table DELETE TOPIC;
-- DROP STREAM IF EXISTS gaming_player_activity_stream;
-- DROP STREAM IF EXISTS gaming_players_stream;
-- DROP STREAM IF EXISTS gaming_games_stream;
