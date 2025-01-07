"""Kafka consumer for processing flight events."""
import json
import logging
import threading
from typing import Optional, Callable, Dict, Any

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from inflight_agentics.config.settings import KAFKA_BROKER_URL, KAFKA_TOPIC, MAX_RETRIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightEventConsumer:
    """Consumer for processing flight-related events from Kafka."""

    def __init__(
        self,
        broker_url: str = KAFKA_BROKER_URL,
        topic: str = KAFKA_TOPIC,
        group_id: Optional[str] = None,
        event_handler: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Initialize the Kafka consumer.

        Args:
            broker_url (str): Kafka broker URL. Defaults to config value.
            topic (str): Kafka topic to consume from. Defaults to config value.
            group_id (Optional[str]): Consumer group ID. Defaults to None.
            event_handler (Optional[Callable]): Function to handle received events.
        """
        self.broker_url = broker_url
        self.topic = topic
        self.group_id = group_id
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=broker_url,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            max_poll_interval_ms=300000,  # 5 minutes
            max_poll_records=500,
            retry_backoff_ms=1000,
            retries=MAX_RETRIES
        )
        self.event_handler = event_handler or self._default_handler
        self.running = False
        self._consumer_thread = None
        self._closed = False
        logger.info(f"Kafka Consumer initialized for topic: {topic}")

    def _default_handler(self, event_data: Dict[str, Any]):
        """
        Default event handler that logs the received event.

        Args:
            event_data (Dict[str, Any]): The received event data.
        """
        logger.info(f"Received event: {event_data}")

    def _consume_loop(self):
        """Internal method to run the consumption loop."""
        try:
            logger.info("Starting to consume messages...")
            while self.running:
                try:
                    # Poll for messages with a timeout
                    message_batch = self.consumer.poll(timeout_ms=1000)
                    
                    if not message_batch:
                        continue

                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            try:
                                self.event_handler(message.value)
                                logger.debug(
                                    f"Processed message from partition {topic_partition.partition} "
                                    f"at offset {message.offset}"
                                )
                            except Exception as e:
                                logger.error(f"Error processing message: {e}")
                                # Could implement dead letter queue here

                except KafkaError as e:
                    logger.error(f"Kafka error while consuming messages: {e}")
                    # Implement backoff/retry strategy if needed
                    if not self.running:
                        break
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False

    def start(self):
        """Start consuming messages in a separate thread."""
        if self._closed:
            raise RuntimeError("Cannot start a closed consumer")
        self.running = True
        self._consumer_thread = threading.Thread(target=self._consume_loop)
        self._consumer_thread.daemon = True
        self._consumer_thread.start()

    def stop(self):
        """Stop consuming messages and close the consumer."""
        if not self._closed:
            self.running = False
            # Don't join the thread if we're in it
            if (
                self._consumer_thread 
                and self._consumer_thread.is_alive() 
                and threading.current_thread() != self._consumer_thread
            ):
                self._consumer_thread.join(timeout=1.0)
            try:
                self.consumer.close()
                logger.info("Kafka consumer closed successfully")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
            self._closed = True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def __repr__(self) -> str:
        """Return string representation of the consumer."""
        return (
            f"FlightEventConsumer(broker_url={self.broker_url}, "
            f"topic={self.topic}, group_id={self.group_id})"
        )
