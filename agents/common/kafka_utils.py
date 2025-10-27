"""Utilities for Kafka producers and consumers with Avro serialization."""

import json
import os
from typing import Dict, Any, Optional, Callable

# Kafka dependencies are optional for dry-run mode
try:
    from confluent_kafka import Producer, Consumer, KafkaError
    from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
    from confluent_kafka.schema_registry import SchemaRegistryClient
    from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


def get_kafka_config() -> Dict[str, str]:
    """
    Get Kafka configuration from environment variables.

    Returns:
        Dictionary with Kafka connection parameters
    """
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_ENDPOINT')
    api_key = os.getenv('KAFKA_API_KEY')
    api_secret = os.getenv('KAFKA_API_SECRET')

    if not all([bootstrap_servers, api_key, api_secret]):
        raise ValueError("Missing required Kafka environment variables: "
                        "KAFKA_BOOTSTRAP_ENDPOINT, KAFKA_API_KEY, KAFKA_API_SECRET")

    return {
        'bootstrap.servers': bootstrap_servers,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'sasl.username': api_key,
        'sasl.password': api_secret
    }


def get_schema_registry_config() -> Dict[str, str]:
    """
    Get Schema Registry configuration from environment variables.

    Returns:
        Dictionary with Schema Registry connection parameters
    """
    sr_url = os.getenv('SCHEMA_REGISTRY_URL')
    sr_api_key = os.getenv('SCHEMA_REGISTRY_API_KEY')
    sr_api_secret = os.getenv('SCHEMA_REGISTRY_API_SECRET')

    if not all([sr_url, sr_api_key, sr_api_secret]):
        raise ValueError("Missing required Schema Registry environment variables: "
                        "SCHEMA_REGISTRY_URL, SCHEMA_REGISTRY_API_KEY, SCHEMA_REGISTRY_API_SECRET")

    return {
        'url': sr_url,
        'basic.auth.user.info': f'{sr_api_key}:{sr_api_secret}'
    }


def create_avro_producer(schema_str: str) -> tuple[Producer, AvroSerializer]:
    """
    Create a Kafka producer with Avro serialization.

    Args:
        schema_str: Avro schema as a JSON string

    Returns:
        Tuple of (Producer, AvroSerializer)
    """
    kafka_config = get_kafka_config()
    schema_registry_conf = get_schema_registry_config()
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    avro_serializer = AvroSerializer(
        schema_registry_client,
        schema_str,
        lambda obj, ctx: obj  # Simple pass-through for dict objects
    )

    producer = Producer(kafka_config)

    return producer, avro_serializer


def produce_message(producer: Producer,
                   serializer: AvroSerializer,
                   topic: str,
                   key: str,
                   value: Dict[str, Any],
                   callback: Optional[Callable] = None) -> None:
    """
    Produce a message to Kafka with Avro serialization.

    Args:
        producer: Kafka producer instance
        serializer: Avro serializer instance
        topic: Topic name
        key: Message key
        value: Message value (dict matching Avro schema)
        callback: Optional delivery report callback
    """
    string_serializer = StringSerializer('utf_8')

    serialized_key = string_serializer(key)
    serialized_value = serializer(
        value,
        SerializationContext(topic, MessageField.VALUE)
    )

    producer.produce(
        topic=topic,
        key=serialized_key,
        value=serialized_value,
        on_delivery=callback or delivery_report
    )
    producer.flush()


def delivery_report(err, msg):
    """Default delivery report callback."""
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')


def create_avro_consumer(schema_str: str, group_id: str) -> tuple[Consumer, AvroDeserializer]:
    """
    Create a Kafka consumer with Avro deserialization.

    Args:
        schema_str: Avro schema as a JSON string
        group_id: Consumer group ID

    Returns:
        Tuple of (Consumer, AvroDeserializer)
    """
    kafka_config = get_kafka_config()
    kafka_config['group.id'] = group_id
    kafka_config['auto.offset.reset'] = 'earliest'

    schema_registry_conf = get_schema_registry_config()
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    avro_deserializer = AvroDeserializer(
        schema_registry_client,
        schema_str
    )

    consumer = Consumer(kafka_config)

    return consumer, avro_deserializer


def consume_latest_message(consumer: Consumer,
                          deserializer: AvroDeserializer,
                          topic: str,
                          timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """
    Consume the latest message from a compacted topic.

    For compacted topics, we want the latest value for each key.
    This function seeks to the end and reads backwards.

    Args:
        consumer: Kafka consumer instance
        deserializer: Avro deserializer instance
        topic: Topic name
        timeout: Timeout in seconds

    Returns:
        Latest message value as a dict, or None if no message
    """
    consumer.subscribe([topic])

    # For simplicity, just read the latest message
    # In a compacted topic, the latest message should be the current state
    latest_msg = None

    try:
        while True:
            msg = consumer.poll(timeout=timeout)

            if msg is None:
                break

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    break
                else:
                    print(f'Consumer error: {msg.error()}')
                    continue

            # Deserialize
            value = deserializer(
                msg.value(),
                SerializationContext(topic, MessageField.VALUE)
            )

            if value is not None:
                latest_msg = value

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

    return latest_msg
