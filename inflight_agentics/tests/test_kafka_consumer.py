"""Unit tests for Kafka consumer."""
import time
import pytest
from unittest.mock import MagicMock, patch, call
from kafka.errors import KafkaError
from inflight_agentics.kafka_consumer import FlightEventConsumer

@pytest.fixture
def mock_kafka_consumer():
    """Fixture to mock KafkaConsumer."""
    with patch('inflight_agentics.kafka_consumer.KafkaConsumer') as mock:
        # Create a mock instance that will be returned by KafkaConsumer()
        consumer_instance = MagicMock()
        mock.return_value = consumer_instance
        
        # Configure default poll behavior
        consumer_instance.poll.return_value = {}
        
        yield consumer_instance

@pytest.fixture
def mock_message():
    """Fixture to create a mock Kafka message."""
    message = MagicMock()
    message.value = {
        "flight_id": "AC1234",
        "status": "DELAYED",
        "timestamp": "2025-01-07T10:00:00Z"
    }
    message.offset = 1
    return message

@pytest.fixture
def mock_topic_partition():
    """Fixture to create a mock TopicPartition."""
    topic_partition = MagicMock()
    topic_partition.topic = "test-topic"
    topic_partition.partition = 0
    return topic_partition

def test_consumer_initialization():
    """Test consumer initialization with default settings."""
    with patch('inflight_agentics.kafka_consumer.KafkaConsumer') as mock_kafka:
        consumer = FlightEventConsumer()
        
        # Verify KafkaConsumer was initialized with correct parameters
        mock_kafka.assert_called_once()
        call_kwargs = mock_kafka.call_args.kwargs
        assert 'bootstrap_servers' in call_kwargs
        assert 'group_id' in call_kwargs
        assert 'value_deserializer' in call_kwargs
        assert 'auto_offset_reset' in call_kwargs
        assert call_kwargs['auto_offset_reset'] == 'earliest'

def test_default_handler(mock_kafka_consumer):
    """Test the default event handler."""
    consumer = FlightEventConsumer()
    test_event = {"test": "data"}
    
    # Should not raise any exceptions
    consumer._default_handler(test_event)

def test_custom_handler_called(mock_kafka_consumer, mock_message, mock_topic_partition):
    """Test that custom event handler is called correctly."""
    mock_handler = MagicMock()
    consumer = FlightEventConsumer(event_handler=mock_handler)
    
    # Configure poll to return one message then empty
    mock_kafka_consumer.poll.side_effect = [
        {mock_topic_partition: [mock_message]},
        {}  # Second poll returns empty to stop the loop
    ]
    
    # Start consumer and let it process messages
    consumer.start()
    time.sleep(0.1)  # Give the consumer thread time to process
    consumer.running = False  # Signal thread to stop
    time.sleep(0.1)  # Give thread time to stop
    consumer.stop()
    
    # Verify handler was called with correct data
    mock_handler.assert_called_once_with(mock_message.value)

def test_consumer_handles_poll_error(mock_kafka_consumer):
    """Test handling of poll errors."""
    consumer = FlightEventConsumer()
    mock_kafka_consumer.poll.side_effect = [
        KafkaError("Poll failed"),
        {}  # Second poll returns empty to stop the loop
    ]
    
    # Should not raise exception
    consumer.start()
    time.sleep(0.1)  # Give the consumer thread time to process
    consumer.running = False  # Signal thread to stop
    time.sleep(0.1)  # Give thread time to stop
    consumer.stop()
    
    # Verify poll was attempted
    mock_kafka_consumer.poll.assert_called()

def test_consumer_handles_handler_error(mock_kafka_consumer, mock_message, mock_topic_partition):
    """Test handling of event handler errors."""
    mock_handler = MagicMock(side_effect=Exception("Handler failed"))
    consumer = FlightEventConsumer(event_handler=mock_handler)
    
    mock_kafka_consumer.poll.side_effect = [
        {mock_topic_partition: [mock_message]},
        {}  # Second poll returns empty to stop the loop
    ]
    
    # Should not raise exception
    consumer.start()
    time.sleep(0.1)  # Give the consumer thread time to process
    consumer.running = False  # Signal thread to stop
    time.sleep(0.1)  # Give thread time to stop
    consumer.stop()
    
    # Verify handler was called despite error
    mock_handler.assert_called_once()

def test_consumer_stop(mock_kafka_consumer):
    """Test consumer stop functionality."""
    consumer = FlightEventConsumer()
    consumer.start()
    time.sleep(0.1)  # Give thread time to start
    consumer.stop()
    
    assert not consumer.running
    mock_kafka_consumer.close.assert_called_once()

def test_consumer_context_manager(mock_kafka_consumer):
    """Test consumer usage as context manager."""
    with FlightEventConsumer() as consumer:
        assert not consumer.running  # Consumer should not auto-start
        consumer.start()  # Start the consumer
        time.sleep(0.1)  # Give thread time to start
    
    # Verify consumer was closed
    mock_kafka_consumer.close.assert_called_once()

def test_consumer_handles_close_error(mock_kafka_consumer):
    """Test handling of errors during consumer closure."""
    mock_kafka_consumer.close.side_effect = Exception("Close failed")
    
    consumer = FlightEventConsumer()
    consumer.start()
    time.sleep(0.1)  # Give thread time to start
    consumer.running = False  # Signal thread to stop
    time.sleep(0.1)  # Give thread time to stop
    # Should not raise exception
    consumer.stop()
    
    mock_kafka_consumer.close.assert_called_once()

def test_consumer_processes_multiple_messages(mock_kafka_consumer, mock_message, mock_topic_partition):
    """Test processing of multiple messages in a batch."""
    mock_handler = MagicMock()
    consumer = FlightEventConsumer(event_handler=mock_handler)
    
    # Create multiple messages
    message1 = MagicMock(value={"id": 1})
    message2 = MagicMock(value={"id": 2})
    
    # Configure poll to return multiple messages then empty
    mock_kafka_consumer.poll.side_effect = [
        {mock_topic_partition: [message1, message2]},
        {}  # Second poll returns empty to stop the loop
    ]
    
    # Start consumer and let it process messages
    consumer.start()
    time.sleep(0.1)  # Give the consumer thread time to process
    consumer.running = False  # Signal thread to stop
    time.sleep(0.1)  # Give thread time to stop
    consumer.stop()
    
    # Verify handler was called for each message
    assert mock_handler.call_count == 2
    mock_handler.assert_has_calls([
        call({"id": 1}),
        call({"id": 2})
    ])

def test_consumer_str_representation():
    """Test string representation of consumer."""
    with patch('inflight_agentics.kafka_consumer.KafkaConsumer'):
        consumer = FlightEventConsumer(
            broker_url="test:9092",
            topic="test-topic",
            group_id="test-group"
        )
        repr_str = repr(consumer)
        
        assert "test:9092" in repr_str
        assert "test-topic" in repr_str
        assert "test-group" in repr_str

def test_consumer_with_custom_config():
    """Test consumer initialization with custom configuration."""
    with patch('inflight_agentics.kafka_consumer.KafkaConsumer') as mock_kafka:
        custom_config = {
            "broker_url": "custom:9092",
            "topic": "custom-topic",
            "group_id": "custom-group"
        }
        
        consumer = FlightEventConsumer(**custom_config)
        
        # Verify custom config was used
        call_kwargs = mock_kafka.call_args.kwargs
        assert call_kwargs['bootstrap_servers'] == "custom:9092"
        assert call_kwargs['group_id'] == "custom-group"
