"""Kafka producer for publishing flight events."""
import json
import logging
from typing import Dict, Any, Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError
from inflight_agentics.config.settings import KAFKA_BROKER_URL, KAFKA_TOPIC, MAX_RETRIES, RETRY_DELAY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightEventProducer:
    """Producer for publishing flight-related events to Kafka."""

    def __init__(self, broker_url: str = KAFKA_BROKER_URL, topic: str = KAFKA_TOPIC):
        """
        Initialize the Kafka producer.

        Args:
            broker_url (str): Kafka broker URL. Defaults to config value.
            topic (str): Kafka topic to publish to. Defaults to config value.
        """
        self.broker_url = broker_url
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=broker_url,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=MAX_RETRIES,
            retry_backoff_ms=int(RETRY_DELAY * 1000)  # Convert to milliseconds
        )
        logger.info(f"Kafka Producer initialized for topic: {self.topic}")

    def publish_event(self, event_data: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        Publish an event to the Kafka topic.

        Args:
            event_data (Dict[str, Any]): Event data to publish.
            key (Optional[str]): Optional key for the message (e.g., flight_id).

        Returns:
            bool: True if published successfully, False otherwise.
        """
        try:
            key_bytes = key.encode('utf-8') if key else None
            future = self.producer.send(self.topic, value=event_data, key=key_bytes)
            
            # Wait for the message to be delivered
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Event published successfully to {record_metadata.topic} "
                f"[partition: {record_metadata.partition}, offset: {record_metadata.offset}]"
            )
            return True

        except KafkaError as e:
            logger.error(f"Failed to publish event: {e}")
            return False

        finally:
            # Ensure all messages are sent
            self.producer.flush()

    def close(self):
        """Close the producer connection."""
        try:
            self.producer.close()
            logger.info("Kafka producer closed successfully")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """Return string representation of the producer."""
        return f"FlightEventProducer(broker_url={self.broker_url}, topic={self.topic})"
